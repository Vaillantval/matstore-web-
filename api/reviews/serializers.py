from rest_framework import serializers

from api.models import Review
from shop.models.Product import Product


class ReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True, required=False
    )

    class Meta:
        model = Review
        fields = [
            "id", "product", "product_id", "author", "author_name",
            "rating", "comment", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "author", "product", "created_at", "updated_at"]

    def get_author_name(self, obj):
        u = obj.author
        full_name = f"{u.first_name} {u.last_name}".strip()
        return full_name or u.username

    def validate(self, attrs):
        request = self.context["request"]
        product = attrs.get("product")
        if product and not self.instance:
            if Review.objects.filter(product=product, author=request.user).exists():
                raise serializers.ValidationError({"product": "Vous avez déjà laissé un avis pour ce produit."})
        return attrs

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)
