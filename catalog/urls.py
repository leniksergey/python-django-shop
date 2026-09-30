from django.urls import path
from . import views

urlpatterns = [
    path("categories", views.categories),
    path("banners", views.banners),
    path("basket", views.basket),
    path("products/popular", views.popular),
    path("products/limited", views.limited),
    path("product/<int:product_id>", views.product_detail),
]
