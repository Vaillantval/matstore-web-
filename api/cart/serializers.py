from rest_framework import serializers

from api.models import CartItem
from api.products.serializers import ProductListSerializer
from shop.models.Product import Product
from shop.models.Setting import Setting


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_available=True),
        write_only=True,
        source="product",
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "subtotal", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_subtotal(self, obj):
        return round(obj.product.solde_price * obj.quantity, 2)


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_available=True)
    )
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate(self, attrs):
        product = attrs["product_id"]
        quantity = attrs["quantity"]
        if product.stock < quantity:
            raise serializers.ValidationError(
                {"quantity": f"Stock insuffisant. Disponible : {product.stock}"}
            )
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        item = self.context.get("item")
        if item and item.product.stock < value:
            raise serializers.ValidationError(
                f"Stock insuffisant. Disponible : {item.product.stock}"
            )
        return value


class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    subtotal_ht = serializers.FloatField()
    tax_rate = serializers.FloatField()
    tax_amount = serializers.FloatField()
    subtotal_ttc = serializers.FloatField()
    total_items = serializers.IntegerField()
    currency = serializers.CharField()
