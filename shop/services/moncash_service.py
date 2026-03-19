import requests
from django.conf import settings


class MonCashService:
    """Client REST MonCash — sans SDK tiers, basé sur l'API officielle Digicel."""

    _API_HOSTS = {
        "live":    "https://moncashbutton.digicelgroup.com/Api",
        "sandbox": "https://sandbox.moncashbutton.digicelgroup.com/Api",
    }
    _GATEWAY_URLS = {
        "live":    "https://moncashbutton.digicelgroup.com/Moncash-middleware",
        "sandbox": "https://sandbox.moncashbutton.digicelgroup.com/Moncash-middleware",
    }

    # ── Config ────────────────────────────────────────────────────────────────

    @classmethod
    def _config(cls) -> dict:
        return getattr(settings, "MONCASH", {})

    @classmethod
    def is_configured(cls) -> bool:
        mc = cls._config()
        client_id  = mc.get("CLIENT_ID",  "").strip()
        secret_key = mc.get("SECRET_KEY", "").strip()
        return bool(client_id) and bool(secret_key)

    @classmethod
    def get_environment(cls) -> str:
        return cls._config().get("ENVIRONMENT", "sandbox")

    @classmethod
    def _api_host(cls) -> str:
        return cls._API_HOSTS.get(cls.get_environment(), cls._API_HOSTS["sandbox"])

    @classmethod
    def _gateway_url(cls) -> str:
        return cls._GATEWAY_URLS.get(cls.get_environment(), cls._GATEWAY_URLS["sandbox"])

    # ── Auth ──────────────────────────────────────────────────────────────────

    @classmethod
    def get_access_token(cls) -> str:
        """
        POST /oauth/token — authentification Basic client_credentials.
        Retourne l'access_token (valide ~60 s).
        """
        mc         = cls._config()
        client_id  = mc.get("CLIENT_ID",  "").strip()
        secret_key = mc.get("SECRET_KEY", "").strip()

        url = f"{cls._api_host()}/oauth/token"
        response = requests.post(
            url,
            auth=(client_id, secret_key),
            headers={"Accept": "application/json"},
            data={"scope": "read,write", "grant_type": "client_credentials"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    # ── Paiement ──────────────────────────────────────────────────────────────

    @classmethod
    def create_payment(cls, amount: float, order_id: str) -> dict:
        """
        POST /v1/CreatePayment
        Retourne {"payment_token": str, "redirect_url": str}
        """
        token = cls.get_access_token()
        url   = f"{cls._api_host()}/v1/CreatePayment"

        response = requests.post(
            url,
            headers={
                "Accept":        "application/json",
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            json={"amount": amount, "orderId": order_id},
            timeout=30,
        )
        if not response.ok:
            raise Exception(f"MonCash {response.status_code} — {response.text}")
        response.raise_for_status()
        data          = response.json()
        payment_token = data["payment_token"]["token"]
        redirect_url  = f"{cls._gateway_url()}/Payment/Redirect?token={payment_token}"
        return {"payment_token": payment_token, "redirect_url": redirect_url}

    # ── Vérification ──────────────────────────────────────────────────────────

    @classmethod
    def retrieve_transaction(cls, transaction_id: str) -> dict:
        """
        POST /v1/RetrieveTransactionPayment
        Retourne le dict 'payment' : reference, transaction_id, cost, message, payer.
        """
        token = cls.get_access_token()
        url   = f"{cls._api_host()}/v1/RetrieveTransactionPayment"

        response = requests.post(
            url,
            headers={
                "Accept":        "application/json",
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            json={"transactionId": transaction_id},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["payment"]

    @classmethod
    def retrieve_order_payment(cls, order_id: str) -> dict:
        """
        POST /v1/RetrieveOrderPayment
        Retourne le dict 'payment' : reference, transaction_id, cost, message, payer.
        """
        token = cls.get_access_token()
        url   = f"{cls._api_host()}/v1/RetrieveOrderPayment"

        response = requests.post(
            url,
            headers={
                "Accept":        "application/json",
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            json={"orderId": order_id},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["payment"]
