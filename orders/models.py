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
        NEW = "new", "Новый"
        ACCEPTED = "accepted", "Принят"
        PAID = "paid", "Оплачен"
        FAILED = "failed", "Ошибка"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Пользователь",
    )
    status = models.CharField(
        max_length=20, choices=Status, default=Status.NEW,
        verbose_name="Статус",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания",
    )
    full_name = models.CharField(
        max_length=200, blank=True, verbose_name="Ф. И. О.",
    )
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_validator],
        verbose_name="Телефон",
    )
    delivery_type = models.CharField(
        max_length=20, blank=True, verbose_name="Способ доставки",
    )
    payment_type = models.CharField(
        max_length=20, blank=True, verbose_name="Способ оплаты",
    )
    city = models.CharField(max_length=100, blank=True, verbose_name="Город")
    address = models.CharField(
        max_length=255, blank=True, verbose_name="Адрес",
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий к заказу")
    payment_error = models.TextField(
        blank=True, verbose_name="Текст ошибки оплаты",
    )
    archived = models.BooleanField(default=False, verbose_name="Архивирован")

    # Мягкое удаление
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ №{self.pk}"

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
    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE,
        verbose_name="Заказ",
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, verbose_name="Товар",
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Цена",
    )
    count = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], verbose_name="Количество",
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"

    def __str__(self):
        return f"Позиция #{self.pk}: {self.product.title} × {self.count}"
