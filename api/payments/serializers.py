from rest_framework import serializers

from shop.models.Order import Order


class PaymentInitiateSerializer(serializers.Serializer):
    order_id = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    payment_method = serializers.ChoiceField(choices=["moncash", "natcash", "stripe", "offline"])


class PaymentVerifySerializer(serializers.Serializer):
    order_id = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    payment_intent_id = serializers.CharField(required=False, allow_blank=True)


class OfflinePaymentSerializer(serializers.Serializer):
    order_id = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    payment_proof = serializers.ImageField()

    def validate_payment_proof(self, file):
        allowed_types = {'image/jpeg', 'image/jpg', 'image/png'}
        if file.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Format non supporté. Utilisez JPG ou PNG."
            )
        max_size = 5 * 1024 * 1024  # 5 MB
        if file.size > max_size:
            raise serializers.ValidationError(
                "Le fichier est trop volumineux. Taille maximale : 5 MB."
            )
        return file
