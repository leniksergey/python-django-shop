from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class CategoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(archived=False)


class Category(models.Model):
    id: int
    title = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    subcategories: models.QuerySet['Category']
    image = models.ImageField(upload_to="categories/", blank=True)
    archived = models.BooleanField(default=False)

    objects = CategoryManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.title


class ProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(archived=False)


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    count = models.PositiveIntegerField(default=0)
    free_delivery = models.BooleanField(default=False)
    limited = models.BooleanField(default=False)
    sort_index = models.PositiveIntegerField(default=0)
    sold = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    archived = models.BooleanField(default=False)
    objects = ProductManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/")

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"

    def __str__(self):
        return f"Photo: {self.product}"


from django.conf import settings


class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews",
        verbose_name="Товар",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="reviews", verbose_name="Пользователь",
    )
    text = models.TextField(verbose_name="Текст отзыва")
    rate = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        default=5,
        verbose_name="Оценка",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    archived = models.BooleanField(default=False, verbose_name="Архивирован")

    objects = ProductManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user} → {self.product} ({self.rate})"
