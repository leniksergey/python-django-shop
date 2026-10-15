from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import Category, Product, Review

User = get_user_model()


class CategoryModelTest(TestCase):
    def test_str(self):
        category = Category.objects.create(title="Электроника")
        self.assertEqual(str(category), "Электроника")

    def test_archived_hidden_by_default_manager(self):
        Category.objects.create(title="Активная")
        Category.objects.create(title="Архивная", archived=True)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Category.all_objects.count(), 2)

    def test_subcategories(self):
        parent = Category.objects.create(title="Родитель")
        child = Category.objects.create(title="Ребёнок", parent=parent)
        self.assertIn(child, parent.subcategories.all())


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Книги")

    def test_str(self):
        product = Product.objects.create(
            category=self.category, title="Книга", price=Decimal("100.00"),
        )
        self.assertEqual(str(product), "Книга")

    def test_archived_hidden_by_default_manager(self):
        Product.objects.create(
            category=self.category, title="Активный", price=Decimal("10.00"),
        )
        Product.objects.create(
            category=self.category, title="Архивный",
            price=Decimal("10.00"), archived=True,
        )
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.all_objects.count(), 2)

    def test_default_count_is_zero(self):
        product = Product.objects.create(
            category=self.category, title="Товар", price=Decimal("10.00"),
        )
        self.assertEqual(product.count, 0)


class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reviewer", password="pass12345",
        )
        self.category = Category.objects.create(title="Тест")
        self.product = Product.objects.create(
            category=self.category, title="Товар", price=Decimal("10.00"),
        )

    def test_review_linked_to_product(self):
        review = Review.objects.create(
            product=self.product, user=self.user, text="Отлично!",
        )
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.user, self.user)
        self.assertIn(review, self.product.reviews.all())
