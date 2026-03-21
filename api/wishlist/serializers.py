from rest_framework import serializers

from api.models import WishlistItem
from api.products.serializers import ProductListSerializer
from shop.models.Product import Product


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "created_at"]


class AddToWishlistSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    def validate_product_id(self, product):
        user = self.context["request"].user
        if WishlistItem.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError("Ce produit est déjà dans vos favoris.")
        return product
