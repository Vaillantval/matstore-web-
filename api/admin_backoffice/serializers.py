from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.products.serializers import ProductAdminSerializer
from dashboard.models.Adress import Adress
from shop.models.Category import Category
from shop.models.Image import Image
from shop.models.Order import Order
from shop.models.OrderDetail import OrderDetail
from shop.models.Product import Product

User = get_user_model()


class AdminOrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = [
            "id", "product_name", "product_description",
            "solde_price", "regular_price", "quantity",
            "taxe", "sub_total_ht", "sub_total_ttc",
        ]


class AdminOrderSerializer(serializers.ModelSerializer):
    order_details = AdminOrderDetailSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    customer_email = serializers.CharField(source="author.email", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "client_name", "customer_email", "billing_address",
            "shipping_address", "quantity", "taxe", "order_cost",
            "order_cost_ttc", "is_paid", "carrier_name", "carrier_price",
            "payment_method", "stripe_payment_intent", "status", "status_display",
            "order_details", "created_at", "updated_at",
        ]


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    tracking_number = serializers.CharField(required=False, allow_blank=True)


class AdminCustomerSerializer(serializers.ModelSerializer):
    order_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "is_active", "is_staff", "date_joined",
            "order_count", "total_spent", "addresses",
        ]
        read_only_fields = ["id", "date_joined", "order_count", "total_spent", "addresses"]

    def get_order_count(self, obj):
        return obj.order_set.count()

    def get_total_spent(self, obj):
        from django.db.models import Sum
        result = obj.order_set.filter(is_paid=True).aggregate(total=Sum("order_cost_ttc"))
        return round(result["total"] or 0, 2)

    def get_addresses(self, obj):
        from api.addresses.serializers import AddressSerializer
        return AddressSerializer(obj.adresses.all(), many=True).data


class AdminCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image", "is_mega", "product_count", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]

    def get_product_count(self, obj):
        return obj.product_set.count()


class InventoryProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "slug", "stock", "is_available", "solde_price", "regular_price"]


class InventoryUpdateSerializer(serializers.Serializer):
    stock = serializers.IntegerField(min_value=0)
    is_available = serializers.BooleanField(required=False)


class ProductImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["id", "image", "created_at"]
