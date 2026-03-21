import uuid
import traceback

from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from shop.models.Order import Order
from shop.models.Setting import Setting
from shop.models.ExchangeRate import ExchangeRate
import stripe
from shop.services.payment_service import StripeService
from shop.services.moncash_service import MonCashService
from shop.services.cart_service import CartService


# ══════════════════════════════════════════════════════════════════════════════
#  STRIPE
# ══════════════════════════════════════════════════════════════════════════════

def create_payment_intent(request, order_id):
    """Crée un PaymentIntent Stripe et retourne le clientSecret."""
    payment_service = StripeService()

    # Fix #2 : guard — clé None si Stripe absent/désactivé
    private_key = payment_service.get_private_key()
    if not private_key:
        return JsonResponse(
            {"error": "Stripe n'est pas configuré ou est indisponible."},
            status=503,
        )
    stripe.api_key = private_key

    # Stripe : toujours facturer en USD (Stripe accepte HTG mais les comptes
    # standard haïtiens posent problème — on convertit depuis la base_currency)
    setting = Setting.objects.first()
    base_currency = setting.base_currency if setting else "USD"

    # Taux base_currency → USD (1.0 si déjà en USD ou taux introuvable)
    if base_currency == "USD":
        usd_rate = 1.0
    else:
        rate_obj = ExchangeRate.objects.filter(
            base_currency=base_currency, target_currency="USD"
        ).first()
        usd_rate = rate_obj.rate if rate_obj else 1.0

    try:
        order = get_object_or_404(Order, id=order_id)
        amount_usd = order.order_cost_ttc * usd_rate
        amount = int(round(amount_usd * 100))   # centimes USD
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            automatic_payment_methods={"enabled": True},
            metadata={
                "order_id": str(order.id),
                "user_id":  str(order.author_id),
            },
            description=f"matstore — commande #{order.id}",
            receipt_email=order.author.email if order.author_id else None,
        )
        order.stripe_payment_intent = payment_intent["id"]
        order.save()
        return JsonResponse({"clientSecret": payment_intent["client_secret"]})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def payment_success(request):
    """Callback Stripe après paiement réussi."""
    payment_intent_id = request.GET.get("payment_intent")
    if not payment_intent_id:
        return redirect("home")

    try:
        payment_service = StripeService()
        private_key = payment_service.get_private_key()
        if not private_key:
            return redirect("home")
        stripe.api_key = private_key

        payment = stripe.PaymentIntent.retrieve(payment_intent_id)

        if payment.status == "succeeded":
            order = get_object_or_404(Order, stripe_payment_intent=payment_intent_id)
            order.is_paid = True
            order.status = "processing"
            order.payment_method = "Stripe"
            order.save()
            CartService.clear_cart(request)
            request.session.pop("pending_order_id", None)
            return render(request, "shop/payment_success.html", {"order": order})
        else:
            return redirect("home")
    except stripe.error.StripeError as e:
        print(f"Erreur Stripe: {str(e)}")
        return redirect("home")
    except Exception as e:
        print(f"Erreur: {str(e)}")
        return redirect("home")


# ══════════════════════════════════════════════════════════════════════════════
#  MONCASH
# ══════════════════════════════════════════════════════════════════════════════


@require_POST
def moncash_initiate(request, order_id):
    """
    Lance un paiement MonCash :
    1. Récupère la commande
    2. Appelle MonCashService.create_payment() (REST API directe)
    3. Redirige vers la page de paiement MonCash
    """
    if not request.user.is_authenticated:
        messages.error(request, "Vous devez être connecté pour payer avec MonCash.")
        return redirect("checkout")

    order = get_object_or_404(Order, id=order_id, author=request.user, is_paid=False)

    if not MonCashService.is_configured():
        messages.error(request, "MonCash n'est pas configuré sur ce site.")
        return redirect("checkout")

    if order.order_cost_ttc <= 0:
        messages.error(
            request,
            "Le montant de la commande est nul. "
            "Retournez au panier et vérifiez vos produits."
        )
        return redirect("checkout")

    # Conversion vers HTG (MonCash n'accepte que des Gourdes haïtiennes)
    setting = Setting.objects.first()
    base_currency = setting.base_currency if setting else "HTG"
    if base_currency == "HTG":
        amount_htg = round(float(order.order_cost_ttc), 2)
    else:
        rate_obj = ExchangeRate.objects.filter(
            base_currency=base_currency, target_currency="HTG"
        ).first()
        if not rate_obj:
            messages.error(
                request,
                f"Taux de change {base_currency} → HTG introuvable. "
                "Actualisez les taux depuis l'admin (Settings → Actualiser les taux)."
            )
            return redirect("checkout")
        amount_htg = round(float(order.order_cost_ttc) * rate_obj.rate, 2)

    # orderId unique envoyé à MonCash — retrouvé dans payment.reference au callback
    mc_order_id = f"{order.id}-{uuid.uuid4().hex[:8]}"

    try:
        result = MonCashService.create_payment(
            amount=amount_htg,
            order_id=mc_order_id,
        )
        request.session["moncash_mc_order_id"] = mc_order_id
        request.session["moncash_order_id"]    = order.id
        return redirect(result["redirect_url"])

    except Exception as e:
        print("=" * 60)
        print(f"[MonCash ERROR] order_id={order_id}  mc_order_id={mc_order_id}")
        print(f"  Exception type : {type(e).__name__}")
        print(f"  Message        : {str(e)}")
        print(f"  Environment    : {MonCashService.get_environment()}")
        print(f"  Amount         : {round(float(order.order_cost_ttc), 2)}")
        print(traceback.format_exc())
        print("=" * 60)
        messages.error(request, f"Erreur MonCash [{type(e).__name__}] : {str(e) or repr(e)}")
        return redirect("checkout")


def moncash_callback(request):
    """
    Callback MonCash après paiement.
    MonCash redirige ici avec ?transactionId=XXXX
    On vérifie la transaction via REST et on marque la commande comme payée.
    """
    transaction_id = request.GET.get("transactionId")
    if not transaction_id:
        messages.error(request, "Paramètre transactionId manquant.")
        return redirect("checkout")

    try:
        payment = MonCashService.retrieve_transaction(transaction_id)

        if payment.get("message") != "successful":
            messages.error(request, "Paiement MonCash introuvable ou annulé.")
            return redirect("checkout")

        # payment["reference"] = mc_order_id envoyé (ex. "2-a1b2c3d4")
        # On extrait l'order.id depuis le préfixe avant le tiret, avec fallback session
        order = None
        reference = payment.get("reference", "")
        try:
            raw_id = reference.split("-")[0]
            order = Order.objects.filter(id=int(raw_id)).first()
        except (ValueError, IndexError):
            pass

        if not order:
            session_order_id = request.session.get("moncash_order_id")
            if session_order_id:
                order = Order.objects.filter(id=session_order_id).first()

        if not order:
            messages.error(request, "Commande introuvable.")
            return redirect("checkout")

        # Idempotence — déjà payée (ex. double appel du callback)
        if order.is_paid:
            return render(request, "shop/payment_success.html", {"order": order})

        # Vérification du montant payé vs montant attendu (tolérance 1 HTG)
        paid_amount = float(payment.get("cost", 0))
        setting = Setting.objects.first()
        base_currency = setting.base_currency if setting else "HTG"
        if base_currency == "HTG":
            expected_htg = float(order.order_cost_ttc)
        else:
            rate_obj = ExchangeRate.objects.filter(
                base_currency=base_currency, target_currency="HTG"
            ).first()
            expected_htg = float(order.order_cost_ttc) * (rate_obj.rate if rate_obj else 1.0)

        if paid_amount < expected_htg - 1:
            messages.error(
                request,
                f"Montant payé ({paid_amount} HTG) inférieur au montant attendu ({expected_htg:.2f} HTG)."
            )
            return redirect("checkout")

        order.is_paid        = True
        order.status         = "processing"
        order.payment_method = "MonCash"
        order.save()

        CartService.clear_cart(request)
        request.session.pop("pending_order_id",    None)
        request.session.pop("moncash_mc_order_id", None)
        request.session.pop("moncash_order_id",    None)
        return render(request, "shop/payment_success.html", {"order": order})

    except Exception as e:
        messages.error(request, f"Erreur lors de la vérification MonCash : {str(e)}")
        return redirect("checkout")
