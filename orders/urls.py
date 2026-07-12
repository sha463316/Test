from django.urls import path
from . import views

urlpatterns = [
    path("orders/checkout/", views.checkout, name="checkout"),
]
