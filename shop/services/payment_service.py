
from django.conf import settings
from shop.models import Method


class StripeService:
    """
    Fournit les clés Stripe selon la priorité suivante :
      1. Table Method (Admin > Méthodes de paiement) si la ligne existe et is_available=True
      2. Variables d'environnement / settings.py (STRIPE dict) en fallback
    """

    def __init__(self):
        self.method = Method.objects.filter(name='Stripe', is_available=True).first()
        self._stripe_cfg = getattr(settings, 'STRIPE', {})

    # ── Clé publique (publiable) ───────────────────────────────────────────────
    def get_public_key(self):
        if self.method:
            return self.method.prod_public_key if not settings.DEBUG else self.method.test_public_key

        # Fallback .env / settings.py
        if settings.DEBUG:
            return self._stripe_cfg.get('TEST_PUBLIC_KEY') or None
        return self._stripe_cfg.get('LIVE_PUBLIC_KEY') or None

    # ── Clé secrète (privée) ──────────────────────────────────────────────────
    def get_secret_key(self):
        if self.method:
            return self.method.prod_private_key if not settings.DEBUG else self.method.test_private_key

        # Fallback .env / settings.py
        if settings.DEBUG:
            return self._stripe_cfg.get('TEST_SECRET_KEY') or None
        return self._stripe_cfg.get('LIVE_SECRET_KEY') or None

    # Alias rétrocompatible conservé (utilisé dans payment_view.py)
    def get_private_key(self):
        return self.get_secret_key()

    # ── Webhook secret ────────────────────────────────────────────────────────
    def get_webhook_secret(self):
        return self._stripe_cfg.get('WEBHOOK_SECRET') or None

    # ── Vérification rapide ───────────────────────────────────────────────────
    def is_configured(self):
        return bool(self.get_secret_key() and self.get_public_key())
