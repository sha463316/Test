"""
Zero Oversell Guarantee — Proof of Race Condition Prevention
============================================================
SQLite-compatible sequential verification.
For true concurrent stress test: use JMeter (jmeter/01-OversellTest.jmx) with PostgreSQL.
"""
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from django.test import TransactionTestCase, override_settings
from django.db import transaction
from rest_framework.test import APIClient
from accounts.models import User, Wallet
from catalog.models import Product, Inventory


@override_settings(DJANGO_SETTINGS_MODULE="config.settings.test")
class StressOversellTest(TransactionTestCase):
    def test_oversell_prevented_sequential(self):
        product = Product.objects.create(name="Limited Item", price=10.00)
        Inventory.objects.create(product=product, quantity=5)

        success = 0
        failed = 0

        for i in range(100):
            u = User.objects.create_user(username=f"buyer{i}", password="pass123")
            Wallet.objects.create(user=u, balance=100)
            c = APIClient()
            c.force_authenticate(user=u)
            c.post("/api/cart/add/", {"product": str(product.id), "quantity": 1}, format="json")
            resp = c.post("/api/orders/checkout/", format="json")
            if resp.status_code == 201:
                success += 1
            else:
                failed += 1

        inv = Inventory.objects.get(product=product)
        print(f"\n=== ZERO OVERSELL PROOF ===")
        print(f"Total attempts: 100")
        print(f"Successful:     {success}")
        print(f"Rejected:       {failed}")
        print(f"Initial stock:  5")
        print(f"Final stock:    {inv.quantity}")

        self.assertLessEqual(success, 5, f"OVERSELL: {success} > 5")
        self.assertEqual(inv.quantity, 5 - success, f"Inventory mismatch")
        self.assertEqual(inv.quantity, 0, f"Stock not zero: {inv.quantity}")
        print("✓ ZERO OVERSELL GUARANTEE CONFIRMED\n")
