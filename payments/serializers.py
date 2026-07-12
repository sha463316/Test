from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "order", "status", "idempotency_key", "processed_at", "created_at")
        read_only_fields = ("id", "status", "processed_at", "created_at")
