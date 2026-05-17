from django.db import models
from django.conf import settings
from core.models import BaseModel
from catalog.models import Product


class CartItem(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "cart_cartitem"
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username}: {self.product.name} x{self.quantity}"
