from django.urls import path
from . import views

urlpatterns = [
    path("products/", views.product_list, name="product-list"),
    path("inventory/", views.inventory_list, name="inventory-list"),
    path("inventory/<uuid:product_id>/", views.inventory_detail, name="inventory-detail"),
    path("inventory/<uuid:product_id>/restock/", views.inventory_restock, name="inventory-restock"),
]
