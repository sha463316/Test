import logging
from celery import shared_task
from orders.models import Order

logger = logging.getLogger("tasks.invoice")


@shared_task
def generate_invoice(order_id: str):
    try:
        order = Order.objects.get(id=order_id)
        logger.info("invoice.generated", extra={"order_id": order_id, "total": float(order.total)})
        return f"Invoice for order {order_id} generated"
    except Order.DoesNotExist:
        logger.error("invoice.failed", extra={"order_id": order_id, "error": "order_not_found"})
        return None
