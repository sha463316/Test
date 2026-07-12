from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import Product, Inventory
from accounts.models import User, Wallet
from orders.models import Order, OrderItem
from payments.models import Payment
import random
import time
import uuid

PRODUCTS = [
    ("Wireless Mouse", 29.99, 100), ("Mechanical Keyboard", 89.99, 50),
    ("USB-C Hub", 45.50, 75), ("27-inch Monitor", 299.00, 30),
    ("Webcam 4K", 129.99, 40), ("Noise Cancelling Headphones", 199.99, 25),
    ("External SSD 1TB", 149.99, 60), ("Laptop Stand", 39.99, 80),
    ("Ergonomic Chair", 499.99, 15), ("Desk Lamp LED", 34.99, 90),
    ("Smartphone Tripod", 24.99, 120), ("Bluetooth Speaker", 79.99, 45),
    ("Graphics Tablet", 249.99, 20), ("Portable Charger 20000mAh", 59.99, 70),
    ("HDMI Cable 3m", 12.99, 200), ("Micro SD Card 256GB", 44.99, 100),
    ("WiFi Router AX1800", 89.99, 35), ("Mechanical Mouse Pad", 29.99, 65),
    ("USB Microphone", 69.99, 55), ("Ring Light 12-inch", 39.99, 40),
    ("Standing Desk Converter", 249.99, 10), ("Monitor Arm Dual", 79.99, 25),
    ("Cable Management Kit", 19.99, 150), ("Surge Protector", 34.99, 85),
    ("Document Scanner", 189.99, 20), ("Label Printer", 129.99, 30),
    ("Paper Shredder", 59.99, 40), ("Electric Pencil Sharpener", 22.99, 60),
    ("Whiteboard 90x60cm", 49.99, 35), ("Office Desk 140cm", 299.99, 12),
    ("Bookshelf 3-Tier", 89.99, 18), ("Filing Cabinet", 159.99, 14),
    ("Safe Box", 79.99, 22), ("Coffee Maker", 69.99, 28),
    ("Electric Kettle", 39.99, 45), ("Mini Fridge 20L", 129.99, 15),
    ("Air Purifier", 199.99, 10), ("Humidifier", 49.99, 30),
    ("Fan Tower", 89.99, 20), ("Space Heater", 59.99, 25),
    ("Smart Plug 4-Pack", 39.99, 80), ("Smart Bulb Color", 24.99, 100),
    ("Security Camera IP", 79.99, 35), ("Video Doorbell", 149.99, 20),
    ("Smart Lock", 199.99, 15), ("Smoke Detector WiFi", 44.99, 40),
    ("Temperature Sensor", 29.99, 60), ("Motion Sensor", 19.99, 70),
    ("Water Leak Detector", 34.99, 50), ("Smart Thermostat", 129.99, 15),
]

NUM_USERS = 100
NUM_ORDERS = 550
BATCH_SIZE = 500


class Command(BaseCommand):
    help = "Seed database with comprehensive test data for all requirements"

    def add_arguments(self, parser):
        parser.add_argument("--orders", type=int, default=NUM_ORDERS, help="Number of orders to create")
        parser.add_argument("--users", type=int, default=NUM_USERS, help="Number of users to create")
        parser.add_argument("--chunk-size", type=int, default=BATCH_SIZE, help="Chunk size for batch processing test")

    def handle(self, *args, **options):
        total_orders = options["orders"]
        total_users = options["users"]
        chunk_size = options["chunk_size"]

        self.stdout.write("🌱 Seeding comprehensive test data...")
        self._seed_products()
        self._seed_users(total_users)
        self._seed_orders(total_orders, chunk_size)
        self.stdout.write(self.style.SUCCESS(f"✅ Seed complete: {len(PRODUCTS)} products, {total_users} users, {total_orders} orders"))

    def _seed_products(self):
        for name, price, qty in PRODUCTS:
            product, created = Product.objects.get_or_create(name=name, defaults={"price": price})
            Inventory.objects.update_or_create(product=product, defaults={"quantity": qty})
        self.stdout.write(f"  ✓ {len(PRODUCTS)} products with inventory")

    def _seed_users(self, count):
        existing = User.objects.count()
        to_create = count - existing
        if to_create <= 0:
            self.stdout.write(f"  ✓ {count} users already exist")
            return
        users = []
        for i in range(existing, existing + to_create):
            user = User(username=f"seed_user_{i}", email=f"user{i}@example.com")
            user.set_password("pass123")
            users.append(user)
        User.objects.bulk_create(users, ignore_conflicts=True)
        for user in User.objects.filter(username__startswith="seed_user_"):
            Wallet.objects.get_or_create(user=user, defaults={"balance": random.choice([500, 1000, 2000, 5000])})
        self.stdout.write(f"  ✓ {to_create} new users with wallets")

    def _seed_orders(self, count, chunk_size):
        existing_orders = Order.objects.count()
        if existing_orders >= count:
            self.stdout.write(f"  ✓ {existing_orders} orders already exist")
            return

        products = list(Product.objects.all())
        users = list(User.objects.filter(username__startswith="seed_user_"))
        if not users:
            self.stdout.write(self.style.WARNING("  ⚠ No seed users found. Run with --users first."))
            return
        if not products:
            self.stdout.write(self.style.WARNING("  ⚠ No products found."))
            return

        to_create = count - existing_orders
        statuses = [Order.Status.PAID, Order.Status.PAID, Order.Status.PAID, Order.Status.PAID, Order.Status.FAILED]
        created = 0
        batch_orders = []

        for i in range(to_create):
            user = random.choice(users)
            num_items = random.randint(1, 4)
            selected = random.sample(products, min(num_items, len(products)))
            total = 0
            items_data = []
            for p in selected:
                qty = random.randint(1, 3)
                total += p.price * qty
                items_data.append((p, qty))

            order = Order.objects.create(user=user, total=total)
            OrderItem.objects.bulk_create([
                OrderItem(order=order, product=p, quantity=qty, unit_price=p.price)
                for p, qty in items_data
            ])
            status = random.choice(statuses)
            if status == Order.Status.PAID:
                Order.objects.filter(id=order.id).update(status=Order.Status.PAID)
                Payment.objects.create(order=order, idempotency_key=str(uuid.uuid4()), processed_at=time.time())

            created += 1
            batch_orders.append(order)

            if len(batch_orders) >= chunk_size:
                self.stdout.write(f"    Chunk {created // chunk_size}: {len(batch_orders)} orders created")
                batch_orders = []

        if batch_orders:
            self.stdout.write(f"    Final chunk: {len(batch_orders)} orders created")

        total_created = Order.objects.count() - existing_orders
        paid = Order.objects.filter(status=Order.Status.PAID).count()
        failed = Order.objects.filter(status=Order.Status.FAILED).count()
        pending = Order.objects.filter(status=Order.Status.PENDING).count()
        payments = Payment.objects.count()
        self.stdout.write(f"  ✓ {total_created} new orders created ({paid} paid, {failed} failed, {pending} pending)")
        self.stdout.write(f"  ✓ {payments} payments created")
