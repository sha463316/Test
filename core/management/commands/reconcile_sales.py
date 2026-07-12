from django.core.management.base import BaseCommand
from tasks.reconcile import reconcile_sales


class Command(BaseCommand):
    help = "Run daily sales reconciliation"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=1, help="Days back to reconcile")

    def handle(self, *args, **options):
        result = reconcile_sales(days_back=options["days"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Reconciled {result['processed']} orders, revenue: ${result['revenue']}"
            )
        )
