from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from catalog.models import Inventory
from .models import CartItem
from .serializers import CartItemSerializer


@api_view(["POST"])
def add_to_cart(request):
    serializer = CartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product_id = serializer.validated_data["product"].id
    quantity = serializer.validated_data["quantity"]

    try:
        inv = Inventory.objects.get(product_id=product_id)
    except Inventory.DoesNotExist:
        return Response({"error": "product not found"}, status=status.HTTP_404_NOT_FOUND)

    if inv.quantity < quantity:
        return Response(
            {"error": "insufficient stock", "available": inv.quantity},
            status=status.HTTP_400_BAD_REQUEST,
        )

    CartItem.objects.update_or_create(
        user=request.user,
        product_id=product_id,
        defaults={"quantity": quantity},
    )
    return Response({"status": "added"}, status=status.HTTP_201_CREATED)
