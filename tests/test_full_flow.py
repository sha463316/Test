from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from catalog.models import Product, Inventory


@override_settings(DJANGO_SETTINGS_MODULE="config.settings.test")
class FullFlowTest(TransactionTestCase):
    def test_complete_checkout_and_payment(self):
        self.client = APIClient()
        product = Product.objects.create(name="Flow Item", price=15.00)
        Inventory.objects.create(product=product, quantity=100)

        register_resp = self.client.post(
            reverse("register"),
            {"username": "flowuser", "email": "flow@example.com", "password": "pass123"},
            format="json",
        )
        self.assertEqual(register_resp.status_code, status.HTTP_201_CREATED)
        token = register_resp.json()["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        cart_resp = self.client.post(
            reverse("cart-add"),
            {"product": str(product.id), "quantity": 1},
            format="json",
        )
        self.assertEqual(cart_resp.status_code, status.HTTP_201_CREATED)

        checkout_resp = self.client.post(reverse("checkout"), format="json")
        self.assertEqual(checkout_resp.status_code, status.HTTP_201_CREATED)
        order_id = checkout_resp.json()["order_id"]

        pay_resp = self.client.post(
            reverse("pay", args=[order_id]),
            format="json",
        )
        self.assertEqual(pay_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(pay_resp.json()["status"], "paid")
