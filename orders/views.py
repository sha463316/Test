import logging
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from accounts.models import Wallet
from cart.models import CartItem
from catalog.models import Inventory, Product
from .models import Order, OrderItem
from tasks.invoice import generate_invoice
from tasks.notify import send_notification

logger = logging.getLogger("orders")


@api_view(["POST"])
def checkout(request):
    user = request.user
    cart_items = list(CartItem.objects.filter(user=user).select_related("product"))
    if not cart_items:
        return Response({"error": "cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        wallet = Wallet.objects.get(user=user)
    except Wallet.DoesNotExist:
        return Response({"error": "wallet not found"}, status=status.HTTP_404_NOT_FOUND)

    total = sum(item.product.price * item.quantity for item in cart_items)
    if wallet.balance < total:
        return Response(
            {"error": "insufficient balance", "balance": float(wallet.balance), "total": float(total)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    product_ids = [item.product_id for item in cart_items]
    product_map = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

    with transaction.atomic():
        inventory_locks = list(
            Inventory.objects.select_for_update().filter(product_id__in=product_ids)
        )
        wallet_lock = Wallet.objects.select_for_update().get(user=user)

        inv_map = {inv.product_id: inv for inv in inventory_locks}

        for ci in cart_items:
            inv = inv_map.get(ci.product_id)
            if not inv or inv.quantity < ci.quantity:
                return Response(
                    {"error": f"insufficient stock for {ci.product.name}"},
                    status=status.HTTP_409_CONFLICT,
                )

        if wallet_lock.balance < total:
            return Response(
                {"error": "insufficient balance"},
                status=status.HTTP_409_CONFLICT,
            )

        for ci in cart_items:
            inv = inv_map[ci.product_id]
            inv.quantity -= ci.quantity
            inv.save(update_fields=["quantity"])

        wallet_lock.balance -= total
        wallet_lock.save(update_fields=["balance"])

        order = Order.objects.create(user=user, total=total)
        for ci in cart_items:
            OrderItem.objects.create(
                order=order,
                product=ci.product,
                quantity=ci.quantity,
                unit_price=ci.product.price,
            )

        CartItem.objects.filter(user=user).delete()

    logger.info("order.created", extra={"order_id": str(order.id), "user_id": str(user.id), "total": float(total)})

    generate_invoice.delay(str(order.id))
    send_notification.delay(str(order.id))

    return Response(
        {"order_id": str(order.id), "status": "PENDING", "total": float(total)},
        status=status.HTTP_201_CREATED,
    )
