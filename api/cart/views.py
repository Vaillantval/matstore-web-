from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.cart.serializers import (
    AddToCartSerializer,
    CartItemSerializer,
    UpdateCartItemSerializer,
)
from api.exceptions import ApiError
from api.models import CartItem
from shop.models.Setting import Setting


def _build_cart_response(user):
    items = CartItem.objects.filter(user=user).select_related("product").prefetch_related(
        "product__images", "product__categories"
    )
    setting = Setting.objects.first()
    tax_rate = (setting.taxe_rate / 100) if setting else 0
    currency = setting.base_currency if setting else "HTG"

    subtotal_ht = sum(item.product.solde_price * item.quantity for item in items)
    tax_amount = round(subtotal_ht * tax_rate, 2)
    subtotal_ttc = round(subtotal_ht + tax_amount, 2)
    total_items = sum(item.quantity for item in items)

    return {
        "success": True,
        "data": {
            "items": CartItemSerializer(items, many=True).data,
            "subtotal_ht": round(subtotal_ht, 2),
            "tax_rate": setting.taxe_rate if setting else 0,
            "tax_amount": tax_amount,
            "subtotal_ttc": subtotal_ttc,
            "total_items": total_items,
            "currency": currency,
        },
    }


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Panier"], summary="Voir son panier")
    def get(self, request):
        return Response(_build_cart_response(request.user))


class CartAddView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Panier"],
        request=AddToCartSerializer,
        summary="Ajouter un produit au panier",
    )
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        item, created = CartItem.objects.get_or_create(
            user=request.user, product=product, defaults={"quantity": quantity}
        )
        if not created:
            new_qty = item.quantity + quantity
            if product.stock < new_qty:
                raise ApiError("INSUFFICIENT_STOCK", f"Stock insuffisant. Disponible : {product.stock}")
            item.quantity = new_qty
            item.save(update_fields=["quantity"])

        return Response(_build_cart_response(request.user), status=status.HTTP_201_CREATED)


class CartUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Panier"],
        request=UpdateCartItemSerializer,
        summary="Modifier la quantité d'un article",
    )
    def patch(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id, user=request.user)
        except CartItem.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Article introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UpdateCartItemSerializer(data=request.data, context={"item": item})
        serializer.is_valid(raise_exception=True)
        item.quantity = serializer.validated_data["quantity"]
        item.save(update_fields=["quantity"])
        return Response(_build_cart_response(request.user))


class CartRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Panier"], summary="Supprimer un article du panier")
    def delete(self, request, item_id):
        CartItem.objects.filter(id=item_id, user=request.user).delete()
        return Response(_build_cart_response(request.user))


class CartClearView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Panier"], summary="Vider le panier")
    def delete(self, request):
        CartItem.objects.filter(user=request.user).delete()
        return Response({"success": True, "message": "Panier vidé."})
