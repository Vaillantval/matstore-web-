import hashlib
import json
import logging

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exceptions import ApiError
from api.payments.serializers import (
    OfflinePaymentSerializer,
    PaymentInitiateSerializer,
    PaymentVerifySerializer,
)
from shop.models.ExchangeRate import ExchangeRate
from shop.models.Order import Order
from shop.models.Setting import Setting
from shop.services.moncash_service import MonCashService
from shop.services.payment_service import StripeService

logger = logging.getLogger(__name__)


class PaymentInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Paiements"],
        request=PaymentInitiateSerializer,
        summary="Initier un paiement",
        description="Retourne les infos de redirection ou le client_secret selon la méthode.",
    )
    def post(self, request):
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = serializer.validated_data["order_id"]
        method = serializer.validated_data["payment_method"]

        if order.author != request.user and not request.user.is_staff:
            raise ApiError("PERMISSION_DENIED")

        if order.is_paid:
            return Response(
                {"success": False, "error": {"code": "ALREADY_PAID", "message": "Cette commande est déjà payée."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if method == "moncash":
                # MonCash n'accepte que des Gourdes haïtiennes — conversion depuis la base_currency
                setting = Setting.objects.first()
                base_currency = setting.base_currency if setting else "HTG"
                if base_currency == "HTG":
                    amount_htg = round(float(order.order_cost_ttc), 2)
                else:
                    rate_obj = ExchangeRate.objects.filter(
                        base_currency=base_currency, target_currency="HTG"
                    ).first()
                    if not rate_obj:
                        raise ApiError(
                            "PAYMENT_FAILED",
                            f"Taux de change {base_currency} → HTG introuvable. "
                            "Actualisez les taux depuis l'admin (Settings → Actualiser les taux).",
                        )
                    amount_htg = round(float(order.order_cost_ttc) * rate_obj.rate, 2)

                result = MonCashService.create_payment(
                    amount=amount_htg,
                    order_id=str(order.id),
                )
                return Response({
                    "success": True,
                    "data": {
                        "method": "moncash",
                        "redirect_url": result["redirect_url"],
                        "payment_token": result["payment_token"],
                        "order_id": order.id,
                        "amount": amount_htg,
                    },
                })

            elif method == "natcash":
                return Response({
                    "success": True,
                    "data": {
                        "method": "natcash",
                        "message": "Paiement NatCash: composez *202# et suivez les instructions.",
                        "order_id": order.id,
                        "amount": order.order_cost_ttc,
                        "reference": f"MATSTORE-{order.id}",
                    },
                })

            elif method == "stripe":
                import stripe
                stripe_svc = StripeService()
                if not stripe_svc.is_configured():
                    raise ApiError("PAYMENT_FAILED", "Stripe non configuré.")

                # Conversion vers USD (Stripe ne supporte pas HTG sur comptes standard)
                setting = Setting.objects.first()
                base_currency = setting.base_currency if setting else "HTG"

                if base_currency == "USD":
                    usd_rate = 1.0
                else:
                    rate_obj = ExchangeRate.objects.filter(
                        base_currency=base_currency, target_currency="USD"
                    ).first()
                    if not rate_obj:
                        raise ApiError(
                            "PAYMENT_FAILED",
                            f"Taux de change {base_currency} → USD introuvable. "
                            "Actualisez les taux depuis l'admin.",
                        )
                    usd_rate = rate_obj.rate

                amount_usd = order.order_cost_ttc * usd_rate
                amount_cents = int(round(amount_usd * 100))

                stripe.api_key = stripe_svc.get_secret_key()
                intent = stripe.PaymentIntent.create(
                    amount=amount_cents,
                    currency="usd",
                    metadata={"order_id": order.id},
                    description=f"matstore — commande #{order.id}",
                    receipt_email=order.author.email,
                )
                order.stripe_payment_intent = intent["id"]
                order.save(update_fields=["stripe_payment_intent"])
                return Response({
                    "success": True,
                    "data": {
                        "method": "stripe",
                        "client_secret": intent["client_secret"],
                        "public_key": stripe_svc.get_public_key(),
                        "order_id": order.id,
                        "amount_htg": order.order_cost_ttc,
                        "amount_usd": round(amount_usd, 2),
                    },
                })

        except ApiError:
            raise
        except Exception as e:
            logger.error(f"Payment initiate error for order {order.id}: {e}")
            raise ApiError("PAYMENT_FAILED", str(e))


class PaymentVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Paiements"],
        request=PaymentVerifySerializer,
        summary="Vérifier le statut d'un paiement",
    )
    def post(self, request):
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = serializer.validated_data["order_id"]
        if order.author != request.user and not request.user.is_staff:
            raise ApiError("PERMISSION_DENIED")

        method = order.payment_method
        transaction_id = serializer.validated_data.get("transaction_id")
        payment_intent_id = serializer.validated_data.get("payment_intent_id")

        try:
            if method == "moncash":
                if not transaction_id:
                    return Response(
                        {"success": False, "error": {"code": "MISSING_PARAM", "message": "transaction_id requis pour MonCash."}},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                payment = MonCashService.retrieve_transaction(transaction_id)
                if payment.get("message") == "successful":
                    order.is_paid = True
                    order.status = "processing"
                    order.save(update_fields=["is_paid", "status"])
                return Response({"success": True, "data": {"is_paid": order.is_paid, "moncash": payment}})

            elif method == "stripe":
                import stripe
                stripe_svc = StripeService()
                stripe.api_key = stripe_svc.get_secret_key()
                intent_id = payment_intent_id or order.stripe_payment_intent
                if not intent_id:
                    return Response(
                        {"success": False, "error": {"code": "MISSING_PARAM", "message": "payment_intent_id requis."}},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                intent = stripe.PaymentIntent.retrieve(intent_id)
                if intent["status"] == "succeeded":
                    order.is_paid = True
                    order.status = "processing"
                    order.save(update_fields=["is_paid", "status"])
                return Response({"success": True, "data": {"is_paid": order.is_paid, "stripe_status": intent["status"]}})

            else:
                return Response({"success": True, "data": {"is_paid": order.is_paid, "method": method}})

        except ApiError:
            raise
        except Exception as e:
            logger.error(f"Payment verify error for order {order.id}: {e}")
            raise ApiError("PAYMENT_FAILED", str(e))


class OfflinePaymentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["Paiements"],
        request=OfflinePaymentSerializer,
        summary="Soumettre une preuve de paiement hors ligne",
        description=(
            "Upload d'une image (JPG/PNG, max 5 MB) comme preuve de virement ou dépôt. "
            "La commande doit avoir payment_method='offline' et appartenir à l'utilisateur connecté. "
            "L'admin reçoit un email de notification automatiquement."
        ),
    )
    def post(self, request):
        serializer = OfflinePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = serializer.validated_data["order_id"]

        if order.author != request.user and not request.user.is_staff:
            raise ApiError("PERMISSION_DENIED")

        if order.payment_method != "offline":
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_PAYMENT_METHOD",
                        "message": "Cette commande n'utilise pas le paiement hors ligne.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.payment_proof = serializer.validated_data["payment_proof"]
        order.payment_status = "proof_submitted"
        order.save(update_fields=["payment_proof", "payment_status"])

        return Response(
            {
                "success": True,
                "data": {
                    "order_id": order.id,
                    "payment_status": order.payment_status,
                    "message": "Preuve de paiement reçue. L'admin va vérifier et confirmer votre commande.",
                },
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_exempt, name="dispatch")
class MonCashWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(tags=["Paiements"], summary="Webhook MonCash", exclude=True)
    def post(self, request):
        try:
            data = request.data
            order_id = data.get("orderId") or data.get("order_id")
            transaction_id = data.get("transactionId") or data.get("transaction_id")

            if order_id:
                order = Order.objects.filter(id=order_id).first()
                if order and transaction_id:
                    payment = MonCashService.retrieve_transaction(transaction_id)
                    if payment.get("message") == "successful":
                        order.is_paid = True
                        order.status = "processing"
                        order.save(update_fields=["is_paid", "status"])
        except Exception as e:
            logger.error(f"MonCash webhook error: {e}")

        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(tags=["Paiements"], summary="Webhook Stripe", exclude=True)
    def post(self, request):
        import stripe

        stripe_svc = StripeService()
        webhook_secret = stripe_svc.get_webhook_secret()
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        payload = request.body

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.warning(f"Stripe webhook signature invalid: {e}")
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        if event["type"] == "payment_intent.succeeded":
            intent = event["data"]["object"]
            order_id = intent.get("metadata", {}).get("order_id")
            if order_id:
                Order.objects.filter(id=order_id).update(is_paid=True, status="processing")

        return Response({"status": "ok"})
