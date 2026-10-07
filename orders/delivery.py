from django.db import models


class DeliverySettings(models.Model):
    """Настройки стоимости доставки. Singleton — одна запись."""
    express_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=500,
        verbose_name="Стоимость экспресс-доставки",
    )
    free_delivery_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, default=2000,
        verbose_name="Порог бесплатной доставки",
    )
    ordinary_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=200,
        verbose_name="Стоимость обычной доставки ниже порога",
    )

    class Meta:
        verbose_name = "Настройки доставки"
        verbose_name_plural = "Настройки доставки"

    def __str__(self):
        return f"Доставка (экспресс {self.express_price}₽, обычная {self.ordinary_price}₽)"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
