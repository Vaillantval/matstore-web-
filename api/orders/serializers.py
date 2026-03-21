from rest_framework import serializers

from shop.models.Carrier import Carrier
from shop.models.Order import Order
from shop.models.OrderDetail import OrderDetail
from shop.models.Product import Product
from shop.models.Setting import Setting


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_available=True))
    quantity = serializers.IntegerField(min_value=1)


class DeliveryAddressSerializer(serializers.Serializer):
    street = serializers.CharField()
    city = serializers.CharField()
    department = serializers.CharField(required=False, default="")


class CreateOrderSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True, min_length=1)
    payment_method = serializers.ChoiceField(choices=["moncash", "natcash", "stripe"])
    delivery_address = DeliveryAddressSerializer()
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_items(self, items):
        seen = {}
        for item in items:
            pid = item["product_id"].id
            if pid in seen:
                raise serializers.ValidationError(f"Produit {pid} dupliqué dans les articles.")
            seen[pid] = True
        return items

    def validate(self, attrs):
        for item in attrs["items"]:
            product = item["product_id"]
            qty = item["quantity"]
            if product.stock < qty:
                raise serializers.ValidationError(
                    {
                        "items": f"Stock insuffisant pour '{product.name}'. "
                        f"Disponible : {product.stock}, demandé : {qty}"
                    }
                )
        return attrs


class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = [
            "id", "product_name", "product_description",
            "solde_price", "regular_price", "quantity",
            "taxe", "sub_total_ht", "sub_total_ttc",
        ]


class OrderSerializer(serializers.ModelSerializer):
    order_details = OrderDetailSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "client_name", "billing_address", "shipping_address",
            "quantity", "taxe", "order_cost", "order_cost_ttc",
            "is_paid", "carrier_name", "carrier_price",
            "payment_method", "stripe_payment_intent",
            "status", "status_display", "order_details",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class OrderTrackingSerializer(serializers.ModelSerializer):
    """Version allégée pour le suivi public — sans infos sensibles."""
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    items_count = serializers.IntegerField(source="quantity", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "status", "status_display",
            "is_paid", "payment_method",
            "carrier_name", "shipping_address",
            "items_count", "order_cost_ttc",
            "created_at", "updated_at",
        ]
        read_only_fields = fields
