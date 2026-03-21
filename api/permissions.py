from rest_framework.permissions import BasePermission, SAFE_METHODS

from shop.models.Order import Order


class IsAdminUser(BasePermission):
    """Autorise uniquement les utilisateurs is_staff=True."""

    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrAdmin(BasePermission):
    """Autorise le propriétaire de la ressource ou un admin."""

    message = "Vous n'êtes pas autorisé à accéder à cette ressource."

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        owner_fields = ("author", "user", "owner")
        for field in owner_fields:
            if hasattr(obj, field):
                return getattr(obj, field) == request.user
        return False


class HasVerifiedPurchase(BasePermission):
    """Autorise uniquement les utilisateurs ayant commandé et reçu le produit."""

    message = "Vous devez avoir acheté ce produit pour laisser un avis."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        product_id = request.data.get("product") or request.parser_context.get(
            "kwargs", {}
        ).get("pk")
        if not product_id:
            return True
        return Order.objects.filter(
            author=request.user,
            status="delivered",
            order_details__product_name__isnull=False,
        ).exists()
