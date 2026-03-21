from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exceptions import ApiError
from api.orders.serializers import CreateOrderSerializer, OrderSerializer, OrderTrackingSerializer
from api.pagination import StandardResultsPagination
from shop.models.Carrier import Carrier
from shop.models.Order import Order
from shop.models.OrderDetail import OrderDetail
from shop.models.Product import Product
from shop.models.Setting import Setting


def _build_order_from_request(user, validated_data):
    """Creates Order + OrderDetails atomically, decrements stock, returns Order."""
    items_data = validated_data["items"]
    payment_method = validated_data["payment_method"]
    delivery = validated_data["delivery_address"]
    notes = validated_data.get("notes", "")

    setting = Setting.objects.first()
    tax_rate = (setting.taxe_rate / 100) if setting else 0
    currency = setting.base_currency if setting else "HTG"

    carrier = Carrier.objects.first()
    carrier_name = carrier.name if carrier else "Standard"
    carrier_price = carrier.price if carrier else 0.0

    shipping_address = f"{delivery['street']}, {delivery['city']}"
    if delivery.get("department"):
        shipping_address += f", {delivery['department']}"
    if notes:
        shipping_address += f" — {notes}"

    billing_address = shipping_address
    client_name = f"{user.first_name} {user.last_name}".strip() or user.username

    order_cost = 0.0
    total_qty = 0
    details_to_create = []

    for item in items_data:
        product = item["product_id"]
        qty = item["quantity"]
        sub_ht = product.solde_price * qty
        taxe_amount = sub_ht * tax_rate
        sub_ttc = sub_ht + taxe_amount

        order_cost += sub_ht
        total_qty += qty
        details_to_create.append(
            {
                "product": product,
                "product_name": product.name,
                "product_description": product.description,
                "solde_price": product.solde_price,
                "regular_price": product.regular_price,
                "quantity": qty,
                "taxe": round(taxe_amount, 2),
                "sub_total_ht": round(sub_ht, 2),
                "sub_total_ttc": round(sub_ttc, 2),
            }
        )

    total_tax = round(order_cost * tax_rate, 2)
    order_cost_ttc = round(order_cost + total_tax + carrier_price, 2)

    with transaction.atomic():
        # Re-check stock inside transaction
        for d in details_to_create:
            product = Product.objects.select_for_update().get(pk=d["product"].pk)
            if product.stock < d["quantity"]:
                raise ApiError(
                    "INSUFFICIENT_STOCK",
                    f"Stock insuffisant pour '{product.name}'. Disponible : {product.stock}",
                )

        order = Order.objects.create(
            client_name=client_name,
            billing_address=billing_address,
            shipping_address=shipping_address,
            quantity=total_qty,
            taxe=total_tax,
            author=user,
            order_cost=round(order_cost, 2),
            order_cost_ttc=order_cost_ttc,
            is_paid=False,
            carrier_name=carrier_name,
            carrier_price=carrier_price,
            payment_method=payment_method,
            status="pending",
        )

        for d in details_to_create:
            OrderDetail.objects.create(
                order=order,
                product_name=d["product_name"],
                product_description=d["product_description"],
                solde_price=d["solde_price"],
                regular_price=d["regular_price"],
                quantity=d["quantity"],
                taxe=d["taxe"],
                sub_total_ht=d["sub_total_ht"],
                sub_total_ttc=d["sub_total_ttc"],
            )

        # Decrement stock
        for d in details_to_create:
            Product.objects.filter(pk=d["product"].pk).update(
                stock=d["product"].stock - d["quantity"]
            )

    return order


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Commandes"],
        responses={200: OrderSerializer(many=True)},
        summary="Historique des commandes",
    )
    def get(self, request):
        paginator = StandardResultsPagination()
        orders = Order.objects.filter(author=request.user).order_by("-created_at")
        page = paginator.paginate_queryset(orders, request)
        serializer = OrderSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["Commandes"],
        request=CreateOrderSerializer,
        responses={201: OrderSerializer},
        summary="Passer une commande",
    )
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = _build_order_from_request(request.user, serializer.validated_data)
        return Response(
            {"success": True, "data": OrderSerializer(order).data},
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(author=self.request.user).prefetch_related("order_details")

    @extend_schema(tags=["Commandes"], summary="Détail d'une commande")
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({"success": True, "data": self.get_serializer(instance).data})


class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Commandes"], summary="Annuler une commande (si PENDING)")
    def post(self, request, pk):
        from django.db.models import F

        try:
            order = Order.objects.get(pk=pk, author=request.user)
        except Order.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Commande introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if order.status != "pending":
            raise ApiError("ORDER_NOT_CANCELLABLE")

        with transaction.atomic():
            # Restore stock best-effort (OrderDetail stores name snapshot, not FK)
            for detail in order.order_details.all():
                Product.objects.filter(name=detail.product_name).update(
                    stock=F("stock") + detail.quantity
                )
            order.status = "canceled"
            order.save(update_fields=["status"])

        return Response({"success": True, "data": OrderSerializer(order).data})


class OrderTrackingView(APIView):
    permission_classes = []  # Public — pas d'auth requise
    authentication_classes = []

    @extend_schema(
        tags=["Commandes"],
        summary="Suivi de commande public (sans authentification)",
        description="Permet de suivre une commande avec son ID et l'email du client. Expose uniquement les infos de suivi.",
    )
    def get(self, request, pk):
        email = request.query_params.get("email", "").strip().lower()
        if not email:
            return Response(
                {"success": False, "error": {"code": "MISSING_PARAM", "message": "Le paramètre 'email' est requis."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            order = Order.objects.get(pk=pk, author__email__iexact=email)
        except Order.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Commande introuvable. Vérifiez l'ID et l'email."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"success": True, "data": OrderTrackingSerializer(order).data})
