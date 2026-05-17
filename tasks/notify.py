import logging
from celery import shared_task
from orders.models import Order

logger = logging.getLogger("tasks.notify")


@shared_task
def send_notification(order_id: str):
    try:
        order = Order.objects.get(id=order_id)
        logger.info("notification.sent", extra={"order_id": order_id, "user_id": str(order.user_id)})
        return f"Notification for order {order_id} sent"
    except Order.DoesNotExist:
        logger.error("notification.failed", extra={"order_id": order_id, "error": "order_not_found"})
        return None
