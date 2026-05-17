from django.core.management.base import BaseCommand
from catalog.models import Product, Inventory


class Command(BaseCommand):
    help = "Seed database with test products"

    def handle(self, *args, **options):
        products = [
            ("Wireless Mouse", 29.99, 100),
            ("Mechanical Keyboard", 89.99, 50),
            ("USB-C Hub", 45.50, 75),
            ("27-inch Monitor", 299.00, 30),
            ("Webcam 4K", 129.99, 40),
            ("Noise Cancelling Headphones", 199.99, 25),
            ("External SSD 1TB", 149.99, 60),
            ("Laptop Stand", 39.99, 80),
            ("Ergonomic Chair", 499.99, 15),
            ("Desk Lamp LED", 34.99, 90),
            ("Smartphone Tripod", 24.99, 120),
            ("Bluetooth Speaker", 79.99, 45),
            ("Graphics Tablet", 249.99, 20),
            ("Portable Charger 20000mAh", 59.99, 70),
            ("HDMI Cable 3m", 12.99, 200),
            ("Micro SD Card 256GB", 44.99, 100),
            ("WiFi Router AX1800", 89.99, 35),
            ("Mechanical Mouse Pad", 29.99, 65),
            ("USB Microphone", 69.99, 55),
            ("Ring Light 12-inch", 39.99, 40),
            ("Standing Desk Converter", 249.99, 10),
            ("Monitor Arm Dual", 79.99, 25),
            ("Cable Management Kit", 19.99, 150),
            ("Surge Protector", 34.99, 85),
            ("Document Scanner", 189.99, 20),
            ("Label Printer", 129.99, 30),
            ("Paper Shredder", 59.99, 40),
            ("Electric Pencil Sharpener", 22.99, 60),
            ("Whiteboard 90x60cm", 49.99, 35),
            ("Office Desk 140cm", 299.99, 12),
            ("Bookshelf 3-Tier", 89.99, 18),
            ("Filing Cabinet", 159.99, 14),
            ("Safe Box", 79.99, 22),
            ("Coffee Maker", 69.99, 28),
            ("Electric Kettle", 39.99, 45),
            ("Mini Fridge 20L", 129.99, 15),
            ("Air Purifier", 199.99, 10),
            ("Humidifier", 49.99, 30),
            ("Fan Tower", 89.99, 20),
            ("Space Heater", 59.99, 25),
            ("Smart Plug 4-Pack", 39.99, 80),
            ("Smart Bulb Color", 24.99, 100),
            ("Security Camera IP", 79.99, 35),
            ("Video Doorbell", 149.99, 20),
            ("Smart Lock", 199.99, 15),
            ("Smoke Detector WiFi", 44.99, 40),
            ("Temperature Sensor", 29.99, 60),
            ("Motion Sensor", 19.99, 70),
            ("Water Leak Detector", 34.99, 50),
            ("Smart Thermostat", 129.99, 15),
        ]
        for name, price, qty in products:
            product, created = Product.objects.get_or_create(
                name=name, defaults={"price": price}
            )
            Inventory.objects.update_or_create(
                product=product, defaults={"quantity": qty}
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(products)} products"))
