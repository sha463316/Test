import logging
from datetime import datetime, timedelta
from django.db.models import Sum, F
from celery import shared_task
from orders.models import Order, OrderItem

logger = logging.getLogger("tasks.reconcile")

CHUNK_SIZE = 500


@shared_task
def reconcile_sales(days_back: int = 1):
    since = datetime.utcnow() - timedelta(days=days_back)
    qs = Order.objects.filter(status=Order.Status.PAID, created_at__gte=since)
    total_orders = qs.count()
    processed = 0
    total_revenue = 0.0

    logger.info(
        "reconcile.started",
        extra={"days_back": days_back, "total_orders": total_orders},
    )

    while processed < total_orders:
        chunk = list(qs.select_related("user").order_by("created_at")[processed:processed + CHUNK_SIZE])
        if not chunk:
            break

        order_ids = [o.id for o in chunk]
        items = (
            OrderItem.objects.filter(order_id__in=order_ids)
            .values("product__name")
            .annotate(total_qty=Sum("quantity"), revenue=Sum(F("quantity") * F("unit_price")))
        )

        chunk_revenue = sum(float(i["revenue"]) for i in items)
        total_revenue += chunk_revenue
        processed += len(chunk)

        logger.info(
            "reconcile.chunk",
            extra={"chunk_size": len(chunk), "chunk_revenue": round(chunk_revenue, 2)},
        )

    logger.info(
        "reconcile.completed",
        extra={"processed_orders": processed, "total_revenue": round(total_revenue, 2)},
    )

    return {"processed": processed, "revenue": round(total_revenue, 2)}
