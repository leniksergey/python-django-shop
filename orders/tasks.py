from celery import shared_task

from .models import Order


@shared_task
def process_payment(order_id, number):
    order = Order.objects.get(pk=order_id)
    valid = number.isdigit() and int(number) % 2 == 0
    order.status = Order.Status.PAID if valid else Order.Status.FAILED
    order.save()
    return valid
