from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator

from catalog.models import Product
from .delivery import DeliverySettings
from .validators import phone_validator


class SoftDeleteManager(models.Manager):
    """Обычный менеджер: не показывает архивированные заказы."""
    def get_queryset(self):
        return super().get_queryset().filter(archived=False)


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new"
        ACCEPTED = "accepted"
        PAID = "paid"
        FAILED = "failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    status = models.CharField(max_length=20, choices=Status, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_validator],
    )
    delivery_type = models.CharField(max_length=20, blank=True)
    payment_type = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True, verbose_name="Комментарий к заказу")
    payment_error = models.TextField(blank=True, verbose_name="Текст ошибки оплаты")
    archived = models.BooleanField(default=False, verbose_name="Архивирован")

    # Мягкое удаление
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    @property
    def items_total(self):
        """Сумма товаров без доставки."""
        return sum(item.price * item.count for item in self.items.all())

    @property
    def delivery_cost(self):
        """Стоимость доставки по ТЗ."""
        settings_obj = DeliverySettings.get_solo()
        if self.delivery_type == "express":
            return settings_obj.express_price
        if self.delivery_type == "ordinary":
            if self.items_total < settings_obj.free_delivery_threshold:
                return settings_obj.ordinary_price
            return 0
        return 0

    @property
    def total_cost(self):
        """Итого: товары + доставка."""
        return self.items_total + self.delivery_cost


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    count = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"
