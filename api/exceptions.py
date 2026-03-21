from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler


ERROR_CODES = {
    "OUT_OF_STOCK": "Ce produit n'est plus disponible en stock.",
    "INSUFFICIENT_STOCK": "Stock insuffisant pour la quantité demandée.",
    "ORDER_NOT_CANCELLABLE": "Cette commande ne peut plus être annulée.",
    "PAYMENT_FAILED": "Le paiement a échoué. Veuillez réessayer.",
    "INVALID_CREDENTIALS": "Identifiants incorrects.",
    "TOKEN_EXPIRED": "Le token a expiré. Veuillez vous reconnecter.",
    "PERMISSION_DENIED": "Vous n'avez pas la permission d'effectuer cette action.",
}


def custom_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = exception_handler(exc, context)

    if response is not None:
        code = getattr(exc, "default_code", "error").upper()
        message = str(exc.detail) if hasattr(exc, "detail") else str(exc)

        if isinstance(exc.detail, list):
            message = exc.detail[0] if exc.detail else message
        elif isinstance(exc.detail, dict):
            first_key = next(iter(exc.detail))
            first_val = exc.detail[first_key]
            message = (
                f"{first_key}: {first_val[0]}"
                if isinstance(first_val, list)
                else str(first_val)
            )

        response.data = {
            "success": False,
            "error": {
                "code": code,
                "message": str(message),
                "details": exc.detail if isinstance(exc.detail, dict) else {},
            },
        }

    return response


class ApiError(exceptions.APIException):
    def __init__(self, code, detail=None, status_code=None):
        self.status_code = status_code or self._resolve_status(code)
        message = detail or ERROR_CODES.get(code, code)
        self.detail = exceptions._get_error_details(message, code)
        self.default_code = code

    @staticmethod
    def _resolve_status(code):
        mapping = {
            "OUT_OF_STOCK": status.HTTP_409_CONFLICT,
            "INSUFFICIENT_STOCK": status.HTTP_409_CONFLICT,
            "ORDER_NOT_CANCELLABLE": status.HTTP_409_CONFLICT,
            "PAYMENT_FAILED": status.HTTP_402_PAYMENT_REQUIRED,
            "INVALID_CREDENTIALS": status.HTTP_401_UNAUTHORIZED,
            "TOKEN_EXPIRED": status.HTTP_401_UNAUTHORIZED,
            "PERMISSION_DENIED": status.HTTP_403_FORBIDDEN,
        }
        return mapping.get(code, status.HTTP_400_BAD_REQUEST)
