from django.contrib.auth.models import AbstractUser
from django.db import models, connection
from django.db.models import F
from core.models import BaseModel


class User(AbstractUser):
    pass


class Wallet(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)

    def deduct(self, amount) -> bool:
        from django.db.models import F
        return Wallet.objects.filter(id=self.id, balance__gte=amount).update(
            balance=F("balance") - amount
        ) > 0

    class Meta:
        db_table = "accounts_wallet"
