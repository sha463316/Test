from rest_framework import serializers
from .models import CartItem


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("quantity must be at least 1")
        return value
