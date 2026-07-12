from django.urls import path
from . import views

urlpatterns = [
    path("payments/pay/<uuid:order_id>/", views.pay, name="pay"),
]
