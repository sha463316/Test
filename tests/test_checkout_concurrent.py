from django.test import TestCase, override_settings
from django.db import transaction
from accounts.models import User, Wallet
from catalog.models import Product, Inventory
from cart.models import CartItem


@override_settings(DJANGO_SETTINGS_MODULE="config.settings.test")
class CheckoutConcurrencyTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="raceuser", password="pass123")
        Wallet.objects.create(user=self.user, balance=1000)
        self.product = Product.objects.create(name="Race Item", price=10.00)
        Inventory.objects.create(product=self.product, quantity=5)
        CartItem.objects.create(user=self.user, product=self.product, quantity=5)

    def test_wallet_deduct_atomic(self):
        wallet = Wallet.objects.get(user=self.user)
        with transaction.atomic():
            w = Wallet.objects.select_for_update().get(user=self.user)
            self.assertTrue(w.deduct(100))
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, 900)

    def test_wallet_deduct_insufficient(self):
        wallet = Wallet.objects.get(user=self.user)
        with transaction.atomic():
            w = Wallet.objects.select_for_update().get(user=self.user)
            self.assertFalse(w.deduct(9999))
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, 1000)

    def test_inventory_deduct_concurrent_safety(self):
        inv = Inventory.objects.get(product=self.product)
        self.assertEqual(inv.quantity, 5)
        with transaction.atomic():
            locked = Inventory.objects.select_for_update().get(product=self.product)
            locked.quantity -= 1
            locked.save(update_fields=["quantity"])
        inv.refresh_from_db()
        self.assertEqual(inv.quantity, 4)

    def test_insufficient_balance(self):
        self.user.wallet.balance = 1
        self.user.wallet.save(update_fields=["balance"])
        from rest_framework.test import APIClient
        c = APIClient()
        c.force_authenticate(user=self.user)
        resp = c.post("/api/orders/checkout/", format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("insufficient balance", resp.json()["error"])
