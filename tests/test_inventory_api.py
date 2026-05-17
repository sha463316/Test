from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from catalog.models import Product, Inventory
from accounts.models import User, Wallet


@override_settings(DJANGO_SETTINGS_MODULE="config.settings.test")
class InventoryAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="admin", password="pass123")
        Wallet.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)
        self.p1 = Product.objects.create(name="Item A", price=10.00)
        Inventory.objects.create(product=self.p1, quantity=50)
        self.p2 = Product.objects.create(name="Item B", price=20.00)
        Inventory.objects.create(product=self.p2, quantity=5)
        self.p3 = Product.objects.create(name="Item C", price=30.00)
        Inventory.objects.create(product=self.p3, quantity=0)

    def test_inventory_list_all(self):
        resp = self.client.get(reverse("inventory-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 3)

    def test_inventory_list_low_stock_filter(self):
        resp = self.client.get(reverse("inventory-list"), {"low_stock": "10"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.json()
        self.assertEqual(len(results), 2)
        for item in results:
            self.assertLess(item["quantity"], 10)

    def test_inventory_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get(reverse("inventory-list"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_detail(self):
        resp = self.client.get(reverse("inventory-detail", args=[self.p1.id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["quantity"], 50)
        self.assertEqual(resp.json()["product_name"], "Item A")

    def test_inventory_detail_not_found(self):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = self.client.get(reverse("inventory-detail", args=[fake_id]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_restock_success(self):
        resp = self.client.post(
            reverse("inventory-restock", args=[self.p1.id]),
            {"quantity": 10},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        inv = Inventory.objects.get(product=self.p1)
        self.assertEqual(inv.quantity, 60)

    def test_restock_invalid_quantity_zero(self):
        resp = self.client.post(
            reverse("inventory-restock", args=[self.p1.id]),
            {"quantity": 0},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restock_invalid_quantity_negative(self):
        resp = self.client.post(
            reverse("inventory-restock", args=[self.p1.id]),
            {"quantity": -5},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restock_not_found(self):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = self.client.post(
            reverse("inventory-restock", args=[fake_id]),
            {"quantity": 10},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_restock_unauthenticated(self):
        self.client.force_authenticate(user=None)
        resp = self.client.post(
            reverse("inventory-restock", args=[self.p1.id]),
            {"quantity": 10},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
