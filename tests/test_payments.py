from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import User, Wallet
from catalog.models import Product, Inventory
from cart.models import CartItem
from orders.models import Order


@override_settings(DJANGO_SETTINGS_MODULE="config.settings.test")
class PaymentAPITest(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="payuser", password="pass123")
        Wallet.objects.create(user=self.user, balance=500)
        product = Product.objects.create(name="Pay Item", price=25.00)
        Inventory.objects.create(product=product, quantity=10)
        CartItem.objects.create(user=self.user, product=product, quantity=2)
        self.client.force_authenticate(user=self.user)

        resp = self.client.post(reverse("checkout"), format="json")
        self.order_id = resp.json()["order_id"]
        self.order = Order.objects.get(id=self.order_id)

    def test_payment_success(self):
        resp = self.client.post(
            reverse("pay", args=[self.order_id]),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["status"], "paid")

    def test_payment_idempotency(self):
        resp1 = self.client.post(
            reverse("pay", args=[self.order_id]),
            {"idempotency_key": "key-123"},
            format="json",
        )
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)

        resp2 = self.client.post(
            reverse("pay", args=[self.order_id]),
            {"idempotency_key": "key-123"},
            format="json",
        )
        self.assertIn(resp2.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        if resp2.status_code == status.HTTP_200_OK:
            self.assertEqual(resp2.json()["status"], "paid")
        else:
            self.assertIn("already", resp2.json().get("error", ""))
