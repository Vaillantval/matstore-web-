from rest_framework import serializers

from api.products.serializers import ProductListSerializer
from shop.models.Category import Category
from shop.models.Product import Product


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image", "is_mega", "product_count", "created_at"]

    def get_product_count(self, obj):
        return obj.product_set.filter(is_available=True).count()


class CategoryDetailSerializer(CategorySerializer):
    products = serializers.SerializerMethodField()

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ["products"]

    def get_products(self, obj):
        qs = Product.objects.filter(
            categories=obj, is_available=True
        ).prefetch_related("images", "categories", "reviews").order_by("-created_at")[:20]
        return ProductListSerializer(qs, many=True).data
