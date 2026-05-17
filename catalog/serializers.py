from rest_framework import serializers
from .models import Product, Inventory


class ProductSerializer(serializers.ModelSerializer):
    stock = serializers.IntegerField(source="inventory.quantity", read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "price", "description", "stock", "created_at")


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_id = serializers.UUIDField(source="product.id", read_only=True)

    class Meta:
        model = Inventory
        fields = ("product_id", "product_name", "quantity", "created_at", "updated_at")


class RestockSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("quantity must be at least 1")
        return value
