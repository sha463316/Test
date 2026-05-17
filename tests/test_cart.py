from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from catalog.models import Product, Inventory
from accounts.models import User, Wallet


@override_settings(DJANGO_SETTINGS_MODULE="config.settings.test")
class CartAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="cartuser", password="pass123")
        Wallet.objects.create(user=self.user)
        self.product = Product.objects.create(name="Cart Item", price=9.99)
        Inventory.objects.create(product=self.product, quantity=10)
        self.client.force_authenticate(user=self.user)

    def test_add_to_cart(self):
        resp = self.client.post(
            reverse("cart-add"),
            {"product": str(self.product.id), "quantity": 2},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_add_insufficient_stock(self):
        resp = self.client.post(
            reverse("cart-add"),
            {"product": str(self.product.id), "quantity": 999},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
