import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from catalog.models import Product
from catalog.views import product_short
from .models import Order, OrderItem

ORDER_FIELDS = {
    "fullName": "full_name",
    "email": "email",
    "phone": "phone",
    "deliveryType": "delivery_type",
    "paymentType": "payment_type",
    "city": "city",
    "address": "address",
}


def serialize_order(order):
    products = []
    for item in order.items.select_related("product"):
        data = product_short(item.product)
        data.update(price=float(item.price), count=item.count)
        products.append(data)
    return {
        "id": order.pk,
        "createdAt": order.created_at.strftime("%Y-%m-%d %H:%M"),
        "fullName": order.full_name,
        "email": order.email,
        "phone": order.phone,
        "deliveryType": order.delivery_type,
        "paymentType": order.payment_type,
        "totalCost": float(order.total_cost),
        "status": order.status,
        "city": order.city,
        "address": order.address,
        "products": products,
    }


def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == "POST":
        body = json.loads(request.body)
        for key, attribute in ORDER_FIELDS.items():
            if key in body:
                setattr(order, attribute, body[key])
        order.status = Order.Status.ACCEPTED
        order.save()
    data = serialize_order(order)
    if request.method == "POST":
        data["orderId"] = order.pk
    return JsonResponse(data)


def orders(request):
    if request.method == "POST":
        return create_order(request)
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)
    user_orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return JsonResponse([serialize_order(order) for order in user_orders], safe=False)


def create_order(request):
    items = json.loads(request.body)
    products = Product.objects.in_bulk([item["id"] for item in items])
    if not items or len(products) != len({item["id"] for item in items}):
        return JsonResponse({"error": "invalid items"}, status=400)
    user = request.user if request.user.is_authenticated else None
    with transaction.atomic():
        order = Order.objects.create(user=user)
        OrderItem.objects.bulk_create(
            OrderItem(
                order=order,
                product=products[item["id"]],
                price=products[item["id"]].price,
                count=item["count"],
            )
            for item in items
        )
    return JsonResponse({"orderId": order.pk})


def is_card_valid(number):
    return number.isdigit() and int(number) % 2 == 0


def payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    body = json.loads(request.body)
    number = "".join(char for char in str(body.get("number", "")) if char.isdigit())
    if not is_card_valid(number):
        order.status = Order.Status.FAILED
        order.save()
        return JsonResponse({"error": "payment failed"}, status=500)
    order.status = Order.Status.PAID
    order.save()
    request.session["basket"] = {}
    return JsonResponse({})
