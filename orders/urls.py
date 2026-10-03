from django.urls import path
from . import views

urlpatterns = [
    path("orders", views.orders),
    path("order/<int:order_id>", views.order_detail),
    path("payment/<int:order_id>", views.payment),
]
