import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from catalog.models import Inventory
from .models import CartItem
from .serializers import CartItemSerializer

logger = logging.getLogger("cart")


@api_view(["POST"])
def add_to_cart(request):
    correlation_id = getattr(request, "correlation_id", None)
    serializer = CartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product_id = serializer.validated_data["product"].id
    quantity = serializer.validated_data["quantity"]
    user_id = str(request.user.id)

    try:
        inv = Inventory.objects.get(product_id=product_id)
    except Inventory.DoesNotExist:
        logger.warning("cart.product_not_found", extra={
            "product_id": str(product_id), "user_id": user_id, "correlation_id": correlation_id,
        })
        return Response({"error": "product not found"}, status=status.HTTP_404_NOT_FOUND)

    if inv.quantity < quantity:
        logger.info("cart.insufficient_stock", extra={
            "product_id": str(product_id), "user_id": user_id,
            "requested": quantity, "available": inv.quantity, "correlation_id": correlation_id,
        })
        return Response(
            {"error": "insufficient stock", "available": inv.quantity},
            status=status.HTTP_400_BAD_REQUEST,
        )

    CartItem.objects.update_or_create(
        user=request.user,
        product_id=product_id,
        defaults={"quantity": quantity},
    )
    logger.info("cart.item_added", extra={
        "product_id": str(product_id), "quantity": quantity,
        "user_id": user_id, "correlation_id": correlation_id,
    })
    return Response({"status": "added"}, status=status.HTTP_201_CREATED)
