from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class CategoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(archived=False)


class Category(models.Model):
    id: int
    title = models.CharField(max_length=255, verbose_name="Название")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Родительская категория",
    )
    subcategories: models.QuerySet['Category']
    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        verbose_name="Изображение",
    )
    archived = models.BooleanField(default=False, verbose_name="Архивирована")

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
        Category, on_delete=models.PROTECT, related_name="products",
        verbose_name="Категория",
    )
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    count = models.PositiveIntegerField(default=0, verbose_name="Количество")
    free_delivery = models.BooleanField(
        default=False, verbose_name="Бесплатная доставка",
    )
    limited = models.BooleanField(
        default=False, verbose_name="Ограниченный тираж",
    )
    sort_index = models.PositiveIntegerField(
        default=0, verbose_name="Индекс сортировки",
    )
    sold = models.PositiveIntegerField(default=0, verbose_name="Продано")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания",
    )
    archived = models.BooleanField(default=False, verbose_name="Архивирован")
    objects = ProductManager()
    all_objects = models.Manager()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Цена",
    )

    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Цена со скидкой",
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE,
        verbose_name="Товар",
    )
    image = models.ImageField(upload_to="products/", verbose_name="Изображение")

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"

    def __str__(self):
        return f"Photo: {self.product}"


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
