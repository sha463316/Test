from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient
from accounts.models import User, Wallet
from catalog.models import Product, Inventory
from cart.models import CartItem
from orders.models import Order, OrderItem
from payments.models import Payment
from tasks.invoice import generate_invoice
from tasks.notify import send_notification
from tasks.reconcile import reconcile_sales
import time
import uuid


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
        Inventory.objects.create(product=product, quantity=500)
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

    def test_reconcile_sales_single(self):
        Order.objects.filter(id=self.order_id).update(status="PAID")
        result = reconcile_sales(days_back=7)
        self.assertEqual(result["processed"], 1)
        self.assertGreater(result["revenue"], 0)

    def test_reconcile_sales_multiple_chunks(self):
        for i in range(10):
            u = User.objects.create_user(username=f"batch_user_{i}", password="pass123")
            Wallet.objects.create(user=u, balance=1000)
            p = Product.objects.create(name=f"Batch Item {i}", price=10.00)
            Inventory.objects.create(product=p, quantity=100)
            for j in range(6):
                o = Order.objects.create(user=u, total=10.00)
                OrderItem.objects.create(order=o, product=p, quantity=1, unit_price=10.00)
                Order.objects.filter(id=o.id).update(status=Order.Status.PAID)
                Payment.objects.create(order=o, idempotency_key=str(uuid.uuid4()), processed_at=time.time())
        result = reconcile_sales(days_back=7)
        self.assertEqual(result["processed"], 60, f"Expected 60 paid orders, got {result['processed']}")
        self.assertEqual(result["revenue"], 600.0, f"Expected revenue 600.0, got {result['revenue']}")
