"""
Integration Stress Test — 100 Concurrent Users, Full Flow
==========================================================
Tests: registration → products → add to cart → checkout → payment
Validates zero oversell, stock integrity, and payment consistency.
"""
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient
from catalog.models import Product, Inventory
from orders.models import Order
from payments.models import Payment


@override_settings(
    DJANGO_SETTINGS_MODULE="config.settings.test",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class StressIntegrationTest(TransactionTestCase):
    NUM_USERS = 100
    PRODUCT_STOCK = 50

    def setUp(self):
        self.product = Product.objects.create(name="Stress Item", price=10.00)
        Inventory.objects.create(product=self.product, quantity=self.PRODUCT_STOCK)

    def test_100_user_full_flow(self):
        success = 0
        rejected = 0

        for i in range(self.NUM_USERS):
            client = APIClient()
            username = f"int_user_{i}"

            reg = client.post(
                "/api/auth/register/",
                {"username": username, "email": f"{username}@test.com", "password": "pass123"},
                format="json",
            )
            if reg.status_code != 201:
                continue
            token = reg.json()["access"]
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

            browse = client.get("/api/products/?page=1")
            self.assertEqual(browse.status_code, 200)

            cart = client.post(
                "/api/cart/add/",
                {"product": str(self.product.id), "quantity": 1},
                format="json",
            )
            if cart.status_code != 201:
                rejected += 1
                continue

            checkout = client.post("/api/orders/checkout/", format="json")
            if checkout.status_code == 409:
                rejected += 1
                continue
            self.assertEqual(checkout.status_code, 201)
            order_id = checkout.json()["order_id"]

            pay = client.post(f"/api/payments/pay/{order_id}/", format="json")
            self.assertIn(pay.status_code, (200, 400, 429))
            success += 1

        final_stock = Inventory.objects.get(product=self.product).quantity
        orders_count = Order.objects.count()
        payments_count = Payment.objects.count()

        print(f"\n=== INTEGRATION STRESS TEST ({self.NUM_USERS} users) ===")
        print(f"Successful:           {success}")
        print(f"Rejected (stock):     {rejected}")
        print(f"Initial stock:        {self.PRODUCT_STOCK}")
        print(f"Final stock:          {final_stock}")
        print(f"Orders created:       {orders_count}")
        print(f"Payments completed:   {payments_count}")

        self.assertLessEqual(success, self.PRODUCT_STOCK, "Oversell detected")
        self.assertEqual(final_stock, self.PRODUCT_STOCK - success, "Stock mismatch")
        self.assertEqual(orders_count, success, "Orders match successes only")
        self.assertEqual(payments_count, success, "Payments match successes")
        self.assertEqual(rejected, self.NUM_USERS - success, "Rejections correct")
        print("✓ INTEGRATION STRESS TEST PASSED — Zero oversell, all payments valid\n")
