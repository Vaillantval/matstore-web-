import uuid
import traceback

from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.http import JsonResponse

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


def moncash_initiate(request, order_id):
    """
    Lance un paiement MonCash :
    1. Récupère la commande (vérification auteur)
    2. Appelle init_payment() du SDK
    3. Redirige le user vers la page de paiement MonCash
    """
    if not request.user.is_authenticated:
        return redirect("checkout")

    order = get_object_or_404(Order, id=order_id, author=request.user, is_paid=False)

    if not MonCashService.is_configured():
        messages.error(request, "MonCash n'est pas configuré sur ce site.")
        return redirect("checkout")

    from django_moncash.utils import init_payment

    # Identifiant unique de transaction MonCash (max 50 chars)
    mc_order_id = f"ord{order.id}_{uuid.uuid4().hex[:8]}"

    # URL de retour après paiement MonCash
    callback_url = request.build_absolute_uri(reverse("moncash_callback"))

    try:
        payment = init_payment(
            request,
            amount=round(order.order_cost_ttc, 2),
            return_url=callback_url,
            order_id=mc_order_id,
            meta_data={"order_id": order.id},
        )
        request.session["moncash_mc_order_id"] = mc_order_id
        request.session["moncash_order_id"]    = order.id
        return redirect(payment["payment_url"])

    except Exception as e:
        # Log complet dans la console Django pour débogage
        print("=" * 60)
        print(f"[MonCash ERROR] order_id={order_id}  mc_order_id={mc_order_id}")
        print(f"  Exception type : {type(e).__name__}")
        print(f"  Message        : {str(e)}")
        print(f"  Environment    : {MonCashService.get_environment()}")
        print(f"  Amount         : {round(order.order_cost_ttc, 2)}")
        print(traceback.format_exc())
        print("=" * 60)
        messages.error(request, f"Erreur MonCash : {str(e)}")
        return redirect("checkout")


def moncash_callback(request):
    """
    Callback MonCash après paiement.
    MonCash redirige ici avec ?transactionId=XXXX
    On consomme la transaction et on marque la commande comme payée.
    """
    from django_moncash.utils import consume_payment

    try:
        result = consume_payment(request)

        if result["success"]:
            order_id = result["payment"]["transaction"].meta_data.get("order_id")
            order = get_object_or_404(Order, id=order_id)
            order.is_paid      = True
            order.status       = "processing"
            order.payment_method = "MonCash"
            order.save()

            CartService.clear_cart(request)
            request.session.pop("pending_order_id",    None)
            request.session.pop("moncash_mc_order_id", None)
            request.session.pop("moncash_order_id",    None)
            return render(request, "shop/payment_success.html", {"order": order})

        elif result.get("error") == "USED":
            # Transaction déjà consommée — on cherche la commande en session
            order_id = request.session.get("moncash_order_id")
            if order_id:
                order = Order.objects.filter(id=order_id, is_paid=True).first()
                if order:
                    return render(request, "shop/payment_success.html", {"order": order})
            return redirect("home")

        else:
            messages.error(request, "Paiement MonCash introuvable ou annulé.")
            return redirect("checkout")

    except Exception as e:
        messages.error(request, f"Erreur lors de la vérification MonCash : {str(e)}")
        return redirect("checkout")
