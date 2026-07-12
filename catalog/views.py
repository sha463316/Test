import logging
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from core.lock import distributed_lock
from .models import Product, Inventory
from .serializers import ProductSerializer, InventorySerializer, RestockSerializer

logger = logging.getLogger("catalog")

CACHE_TTL = 60
PRODUCT_CACHE_PREFIX = "product_list_page_{page}"
INVENTORY_LIST_CACHE_KEY = "inventory_list"
INVENTORY_DETAIL_CACHE_KEY = "inventory_detail_{product_id}"
STAMPEDE_LOCK_PREFIX = "cache_stampede:"


def _get_cid(request):
    return getattr(request, "correlation_id", None)


@api_view(["GET"])
@permission_classes([AllowAny])
def product_list(request):
    correlation_id = _get_cid(request)
    page = request.GET.get("page", "1")
    cache_key = PRODUCT_CACHE_PREFIX.format(page=page)
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info("cache.hit", extra={"cache_key": cache_key, "correlation_id": correlation_id})
        return Response(cached)

    with distributed_lock(f"{STAMPEDE_LOCK_PREFIX}{cache_key}", ttl=10, retry_count=3):
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info("cache.hit_after_lock", extra={"cache_key": cache_key, "correlation_id": correlation_id})
            return Response(cached)
        queryset = Product.objects.select_related("inventory").all().order_by("-created_at")
        paginator = PageNumberPagination()
        paginated = paginator.paginate_queryset(queryset, request)
        serializer = ProductSerializer(paginated, many=True)
        result = paginator.get_paginated_response(serializer.data).data
        cache.set(cache_key, result, CACHE_TTL)
        logger.info("cache.miss", extra={"cache_key": cache_key, "correlation_id": correlation_id})
    return Response(result)


@api_view(["GET"])
def inventory_list(request):
    correlation_id = _get_cid(request)
    low_stock = request.GET.get("low_stock")
    if low_stock is not None:
        try:
            threshold = int(low_stock)
            qs = Inventory.objects.select_related("product").all().order_by("product__name")
            qs = qs.filter(quantity__lt=threshold)
            serializer = InventorySerializer(qs, many=True)
            return Response(serializer.data)
        except ValueError:
            pass
    cached = cache.get(INVENTORY_LIST_CACHE_KEY)
    if cached is not None:
        logger.info("cache.hit", extra={"cache_key": INVENTORY_LIST_CACHE_KEY, "correlation_id": correlation_id})
        return Response(cached)
    qs = Inventory.objects.select_related("product").all().order_by("product__name")
    serializer = InventorySerializer(qs, many=True)
    result = serializer.data
    cache.set(INVENTORY_LIST_CACHE_KEY, result, CACHE_TTL)
    logger.info("cache.miss", extra={"cache_key": INVENTORY_LIST_CACHE_KEY, "correlation_id": correlation_id})
    return Response(result)


@api_view(["GET"])
def inventory_detail(request, product_id):
    correlation_id = _get_cid(request)
    cache_key = INVENTORY_DETAIL_CACHE_KEY.format(product_id=product_id)
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info("cache.hit", extra={"cache_key": cache_key, "correlation_id": correlation_id})
        return Response(cached)
    try:
        inv = Inventory.objects.select_related("product").get(product_id=product_id)
    except Inventory.DoesNotExist:
        return Response({"error": "inventory not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = InventorySerializer(inv)
    result = serializer.data
    cache.set(cache_key, result, CACHE_TTL)
    logger.info("cache.miss", extra={"cache_key": cache_key, "correlation_id": correlation_id})
    return Response(result)


@api_view(["POST"])
def inventory_restock(request, product_id):
    correlation_id = _get_cid(request)
    serializer = RestockSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    lock_key = f"restock_lock:{product_id}"
    with distributed_lock(lock_key, ttl=10, retry_count=5, retry_delay=0.2) as acquired:
        if not acquired:
            return Response(
                {"error": "restock already in progress"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        try:
            inv = Inventory.objects.get(product_id=product_id)
        except Inventory.DoesNotExist:
            return Response({"error": "inventory not found"}, status=status.HTTP_404_NOT_FOUND)

        quantity = serializer.validated_data["quantity"]
        inv.quantity += quantity
        inv.save(update_fields=["quantity"])

        cache_key = INVENTORY_DETAIL_CACHE_KEY.format(product_id=product_id)
        cache.delete(cache_key)
        cache.delete(INVENTORY_LIST_CACHE_KEY)

        logger.info("inventory.restocked", extra={
            "product_id": str(product_id),
            "added": quantity,
            "new_quantity": inv.quantity,
            "correlation_id": correlation_id,
        })

    return Response(
        {"status": "restocked", "product_id": str(product_id), "new_quantity": inv.quantity},
        status=status.HTTP_200_OK,
    )
