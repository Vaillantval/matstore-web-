from django.conf import settings


class MonCashService:
    """Utilitaires pour la méthode de paiement MonCash."""

    @staticmethod
    def is_configured() -> bool:
        """Retourne True si les clés MonCash sont renseignées dans .env/settings."""
        mc = getattr(settings, "MONCASH", {})
        client_id  = mc.get("CLIENT_ID", "").strip()
        secret_key = mc.get("SECRET_KEY", "").strip()
        return (
            bool(client_id)  and client_id  != "your_moncash_client_id_here" and
            bool(secret_key) and secret_key != "your_moncash_secret_key_here"
        )

    @staticmethod
    def get_environment() -> str:
        mc = getattr(settings, "MONCASH", {})
        return mc.get("ENVIRONMENT", "sandbox")
