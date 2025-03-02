from rest_framework import serializers


class AddToOrderSerializer(serializers.Serializer):
    """Сериализатор для добавления товара в заказ."""
    item_id = serializers.IntegerField(required=True)
    order_id = serializers.CharField(required=False, allow_null=True)