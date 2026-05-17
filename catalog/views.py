import logging
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Product, Inventory
from .serializers import ProductSerializer, InventorySerializer, RestockSerializer

logger = logging.getLogger("catalog.inventory")

CACHE_TTL = 60
CACHE_KEY = "product_list_page_{page}"


@api_view(["GET"])
@permission_classes([AllowAny])
def product_list(request):
    page = request.GET.get("page", "1")
    cache_key = CACHE_KEY.format(page=page)
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    queryset = Product.objects.select_related("inventory").all().order_by("-created_at")
    paginator = PageNumberPagination()
    paginated = paginator.paginate_queryset(queryset, request)
    serializer = ProductSerializer(paginated, many=True)
    result = paginator.get_paginated_response(serializer.data).data
    cache.set(cache_key, result, CACHE_TTL)
    return Response(result)


@api_view(["GET"])
def inventory_list(request):
    low_stock = request.GET.get("low_stock")
    qs = Inventory.objects.select_related("product").all().order_by("product__name")
    if low_stock is not None:
        try:
            threshold = int(low_stock)
            qs = qs.filter(quantity__lt=threshold)
        except ValueError:
            pass
    serializer = InventorySerializer(qs, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def inventory_detail(request, product_id):
    try:
        inv = Inventory.objects.select_related("product").get(product_id=product_id)
    except Inventory.DoesNotExist:
        return Response({"error": "inventory not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = InventorySerializer(inv)
    return Response(serializer.data)


@api_view(["POST"])
def inventory_restock(request, product_id):
    serializer = RestockSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        inv = Inventory.objects.get(product_id=product_id)
    except Inventory.DoesNotExist:
        return Response({"error": "inventory not found"}, status=status.HTTP_404_NOT_FOUND)

    quantity = serializer.validated_data["quantity"]
    inv.quantity += quantity
    inv.save(update_fields=["quantity"])

    logger.info("inventory.restocked", extra={
        "product_id": str(product_id),
        "added": quantity,
        "new_quantity": inv.quantity,
    })

    return Response(
        {"status": "restocked", "product_id": str(product_id), "new_quantity": inv.quantity},
        status=status.HTTP_200_OK,
    )
