from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status


@override_settings(DJANGO_SETTINGS_MODULE="config.settings.test")
class AccountsAPITest(TestCase):
    def test_register_and_login(self):
        resp = self.client.post(
            reverse("register"),
            {"username": "testuser", "email": "test@example.com", "password": "pass123"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", resp.json())
        self.assertIn("refresh", resp.json())

        resp = self.client.post(
            reverse("login"),
            {"username": "testuser", "password": "pass123"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.json())

    def test_login_invalid(self):
        resp = self.client.post(
            reverse("login"),
            {"username": "nobody", "password": "wrong"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
