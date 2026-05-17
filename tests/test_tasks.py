from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient
from accounts.models import User, Wallet
from catalog.models import Product, Inventory
from cart.models import CartItem
from orders.models import Order
from tasks.invoice import generate_invoice
from tasks.notify import send_notification
from tasks.reconcile import reconcile_sales


@override_settings(
    DJANGO_SETTINGS_MODULE="config.settings.test",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class TasksTest(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="taskuser", password="pass123")
        Wallet.objects.create(user=self.user, balance=1000)
        product = Product.objects.create(name="Task Item", price=30.00)
        Inventory.objects.create(product=product, quantity=5)
        CartItem.objects.create(user=self.user, product=product, quantity=1)
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/orders/checkout/", format="json")
        self.order_id = resp.json()["order_id"]

    def test_generate_invoice(self):
        result = generate_invoice(self.order_id)
        self.assertIsNotNone(result)
        self.assertIn("generated", result)

    def test_send_notification(self):
        result = send_notification(self.order_id)
        self.assertIsNotNone(result)
        self.assertIn("sent", result)

    def test_reconcile_sales(self):
        Order.objects.filter(id=self.order_id).update(status="PAID")
        result = reconcile_sales(days_back=7)
        self.assertEqual(result["processed"], 1)
        self.assertGreater(result["revenue"], 0)
