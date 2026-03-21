from rest_framework import serializers

from shop.models.Category import Category
from shop.models.Image import Image
from shop.models.Product import Product


class CategoryBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["id", "image"]


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    price = serializers.FloatField(source="solde_price")
    compare_at_price = serializers.FloatField(source="regular_price")
    in_stock = serializers.BooleanField(source="is_available")
    stock_quantity = serializers.IntegerField(source="stock")
    rating_average = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "price", "compare_at_price",
            "currency", "images", "category", "in_stock", "stock_quantity",
            "rating_average", "rating_count", "created_at",
        ]

    def get_category(self, obj):
        first_cat = obj.categories.first()
        if first_cat:
            return CategoryBriefSerializer(first_cat).data
        return None

    def get_rating_average(self, obj):
        reviews = obj.reviews.all()
        if not reviews.exists():
            return None
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)

    def get_rating_count(self, obj):
        return obj.reviews.count()

    def get_currency(self, obj):
        from shop.models.Setting import Setting
        setting = Setting.objects.first()
        return setting.base_currency if setting else "HTG"


class ProductDetailSerializer(ProductListSerializer):
    categories = CategoryBriefSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            "more_description", "additional_info", "brand",
            "is_best_seller", "is_featured", "is_new_arrival",
            "is_special_offer", "categories", "updated_at",
        ]


class ProductAdminSerializer(serializers.ModelSerializer):
    """Serializer pour CRUD admin."""
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "more_description",
            "additional_info", "stock", "solde_price", "regular_price",
            "brand", "is_available", "is_best_seller", "is_featured",
            "is_new_arrival", "is_special_offer", "categories", "images",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]
