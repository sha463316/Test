from django.db import models
from core.models import BaseModel


class Product(BaseModel):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "catalog_product"

    def __str__(self):
        return self.name


class Inventory(BaseModel):
    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name="inventory"
    )
    quantity = models.IntegerField(default=0)

    class Meta:
        db_table = "catalog_inventory"

    def __str__(self):
        return f"{self.product.name}: {self.quantity}"
