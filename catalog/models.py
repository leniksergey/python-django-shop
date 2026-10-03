from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


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

    def __str__(self):
        return self.title


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

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/")

    def __str__(self):
        return f"Фото: {self.product}"
