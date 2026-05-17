import uuid
import time
from django.db import models
from core.models import BaseModel


class Payment(BaseModel):
    order = models.OneToOneField(
        "orders.Order", on_delete=models.CASCADE, related_name="payment"
    )
    status = models.CharField(max_length=20, default="COMPLETED")
    idempotency_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    processed_at = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "payments_payment"

    def __str__(self):
        return f"Payment for Order {self.order_id}: {self.status}"
