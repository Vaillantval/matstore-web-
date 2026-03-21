from rest_framework import serializers

from shop.models.Order import Order


class PaymentInitiateSerializer(serializers.Serializer):
    order_id = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    payment_method = serializers.ChoiceField(choices=["moncash", "natcash", "stripe"])


class PaymentVerifySerializer(serializers.Serializer):
    order_id = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    payment_intent_id = serializers.CharField(required=False, allow_blank=True)
