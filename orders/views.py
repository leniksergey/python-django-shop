import json
import logging

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from catalog.views import product_short
from .forms import OrderCreateForm, OrderUpdateForm, PaymentForm
from .models import Order, OrderItem
from .tasks import process_payment

logger = logging.getLogger(__name__)

ORDER_FIELDS = {
    "fullName": "full_name",
    "email": "email",
    "phone": "phone",
    "deliveryType": "delivery_type",
    "paymentType": "payment_type",
    "city": "city",
    "address": "address",
    "comment": "comment",
}


def _parse_json(request):
    try:
        return json.loads(request.body or "{}"), None
    except json.JSONDecodeError:
        return None, JsonResponse({"error": "invalid json"}, status=400)


def serialize_order(order):
    products = []
    for item in order.items.select_related("product"):
        data = product_short(item.product)
        data.update(price=float(item.price), count=item.count)
        products.append(data)

    full_name = order.full_name
    email = order.email
    phone = order.phone

    if order.user_id:
        user = order.user
        if not email:
            email = user.email or ""
        if not full_name:
            full_name = user.get_full_name() or user.username
        if not phone:
            profile = getattr(user, "profile", None)
            if profile:
                phone = profile.phone or ""

    return {
        "id": order.pk,
        "createdAt": order.created_at.strftime("%Y-%m-%d %H:%M"),
        "fullName": full_name,
        "email": email,
        "phone": phone,
        "deliveryType": order.delivery_type,
        "paymentType": order.payment_type,
        "itemsCost": float(order.items_total),
        "deliveryCost": float(order.delivery_cost),
        "totalCost": float(order.total_cost),
        "status": order.status,
        "paymentError": order.payment_error or None,
        "city": order.city,
        "address": order.address,
        "comment": order.comment,
        "products": products,
    }


def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    if request.method == "POST":
        if order.user_id is not None and order.user_id != request.user.id:
            return JsonResponse({"error": "forbidden"}, status=403)

        # Пока заказ не оплачен — можно редактировать.
        # Но редактирование запрещено, если статус PAID.
        if order.status == Order.Status.PAID:
            return JsonResponse({"error": "order is locked"}, status=409)

        body, err = _parse_json(request)
        if err:
            return err

        form = OrderUpdateForm(body)
        if not form.is_valid():
            return JsonResponse(
                {"error": "validation failed", "errors": form.errors}, status=400
            )

        with transaction.atomic():
            for key, attribute in ORDER_FIELDS.items():
                setattr(order, attribute, form.cleaned_data[key])
            order.status = Order.Status.ACCEPTED
            order.save(update_fields=[*ORDER_FIELDS.values(), "status"])

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
    return JsonResponse([serialize_order(o) for o in user_orders], safe=False)


@require_POST
def create_order(request):
    body, err = _parse_json(request)
    if err:
        return err

    form = OrderCreateForm({"items": body})
    if not form.is_valid():
        return JsonResponse(
            {"error": "validation failed", "errors": form.errors}, status=400
        )

    user = request.user if request.user.is_authenticated else None

    phone = ""
    if user:
        profile = getattr(user, "profile", None)
        if profile:
            phone = profile.phone or ""

    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            email=user.email if user else "",
            full_name=(user.get_full_name() or user.username) if user else "",
            phone=phone,
        )
        OrderItem.objects.bulk_create(
            OrderItem(
                order=order,
                product=product,
                price=product.sale_price or product.price,  # ← правильно!
                count=count,
            )
            for product, count in form.cleaned_data["items"]
        )
    return JsonResponse({"orderId": order.pk})


@require_POST
def payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    if order.user_id is not None and order.user_id != request.user.id:
        return JsonResponse({"error": "forbidden"}, status=403)

    if order.status == Order.Status.PAID:
        return JsonResponse({"error": "already paid"}, status=409)
    if order.status not in (Order.Status.ACCEPTED, Order.Status.FAILED):
        return JsonResponse({"error": "order not accepted"}, status=409)

    body, err = _parse_json(request)
    if err:
        return err

    form = PaymentForm(body)
    if not form.is_valid():
        return JsonResponse(
            {"error": "validation failed", "errors": form.errors}, status=400
        )

    if order.total_cost <= 0:
        return JsonResponse({"error": "invalid amount"}, status=400)

    try:
        result = process_payment.apply_async(
            args=(order.pk, form.cleaned_data["number"]), expires=15
        ).get(timeout=10)
    except Exception:
        logger.exception("payment task failed for order %s", order.pk)
        order.status = Order.Status.FAILED
        order.payment_error = "Платёжный сервис недоступен, попробуйте позже"
        order.save(update_fields=["status", "payment_error"])
        return JsonResponse({"error": "payment service unavailable"}, status=503)

    # process_payment может вернуть:
    #   True / False
    #   или строку с текстом ошибки
    #   или словарь {"success": bool, "error": str}
    if isinstance(result, dict):
        success = result.get("success", False)
        error_text = result.get("error", "")
    elif isinstance(result, str):
        success = False
        error_text = result
    else:
        success = bool(result)
        error_text = "" if success else "Платёж отклонён платёжной системой"

    if not success:
        order.status = Order.Status.FAILED
        order.payment_error = error_text or "Ошибка оплаты"
        order.save(update_fields=["status", "payment_error"])
        return JsonResponse(
            {"error": "payment failed", "paymentError": order.payment_error},
            status=500,
        )

    order.status = Order.Status.PAID
    order.payment_error = ""
    order.save(update_fields=["status", "payment_error"])
    request.session["basket"] = {}
    return JsonResponse({"status": "ok", "orderId": order.pk})
