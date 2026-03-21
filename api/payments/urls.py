from django.urls import path

from api.payments.views import (
    MonCashWebhookView,
    PaymentInitiateView,
    PaymentVerifyView,
    StripeWebhookView,
)

urlpatterns = [
    path("initiate/", PaymentInitiateView.as_view(), name="api-payment-initiate"),
    path("verify/", PaymentVerifyView.as_view(), name="api-payment-verify"),
    path("webhook/moncash/", MonCashWebhookView.as_view(), name="api-webhook-moncash"),
    path("webhook/stripe/", StripeWebhookView.as_view(), name="api-webhook-stripe"),
]
