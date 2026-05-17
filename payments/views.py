import time
import logging
import uuid
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from orders.models import Order
from core.lock import acquire_lock, release_lock
from .models import Payment

logger = logging.getLogger("payments")

LOCK_TTL = 60


@api_view(["POST"])
def pay(request, order_id):
    idempotency_key = request.data.get("idempotency_key", str(uuid.uuid4()))
    lock_key = f"payment_lock:{order_id}"

    if not acquire_lock(lock_key, LOCK_TTL):
        return Response(
            {"error": "payment already being processed"},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    try:
        try:
            order = Order.objects.select_related("payment").get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.status != Order.Status.PENDING:
            return Response(
                {"error": f"order already {order.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hasattr(order, "payment"):
            return Response(
                {"status": "already_paid", "payment_id": str(order.payment.id)},
                status=status.HTTP_200_OK,
            )

        time.sleep(2)

        with transaction.atomic():
            order.status = Order.Status.PAID
            order.save(update_fields=["status"])
            payment = Payment.objects.create(
                order=order,
                idempotency_key=idempotency_key,
                processed_at=time.time(),
            )

        logger.info("payment.completed", extra={"order_id": order_id, "payment_id": str(payment.id)})

        return Response(
            {"status": "paid", "payment_id": str(payment.id)},
            status=status.HTTP_200_OK,
        )
    finally:
        release_lock(lock_key)
