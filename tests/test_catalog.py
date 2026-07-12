from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from catalog.models import Product, Inventory


@override_settings(DJANGO_SETTINGS_MODULE="config.settings.test")
class CatalogAPITest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Test Item", price=19.99)
        Inventory.objects.create(product=self.product, quantity=50)

    def test_product_list_unauthenticated(self):
        resp = self.client.get(reverse("product-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn("results", data)
        self.assertGreaterEqual(len(data["results"]), 1)
        found = [p for p in data["results"] if p["id"] == str(self.product.id)]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["stock"], 50)
