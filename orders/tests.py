from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import Category, Product
from orders.models import Order, OrderItem
from orders.tasks import process_payment

User = get_user_model()


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer", password="pass12345",
        )

    def test_str(self):
        order = Order.objects.create(user=self.user)
        self.assertEqual(str(order), f"Заказ №{order.pk}")

    def test_default_status_is_new(self):
        order = Order.objects.create(user=self.user)
        self.assertEqual(order.status, Order.Status.NEW)

    def test_archived_hidden_by_default_manager(self):
        Order.objects.create(user=self.user)
        Order.objects.create(user=self.user, archived=True)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.all_objects.count(), 2)


class OrderItemTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer2", password="pass12345",
        )
        self.category = Category.objects.create(title="Тест")
        self.product = Product.objects.create(
            category=self.category, title="Товар", price=Decimal("100.00"),
        )
        self.order = Order.objects.create(user=self.user)

    def test_items_total_sums_price_times_count(self):
        OrderItem.objects.create(
            order=self.order, product=self.product,
            price=Decimal("100.00"), count=2,
        )
        OrderItem.objects.create(
            order=self.order, product=self.product,
            price=Decimal("50.00"), count=3,
        )
        self.assertEqual(self.order.items_total, Decimal("350.00"))


class ProcessPaymentTaskTest(TestCase):
    """Проверяем логику фиктивного сервиса оплаты."""

    def test_even_number_without_zero_succeeds(self):
        self.assertTrue(process_payment(order_id=1, number="1234"))

    def test_odd_number_fails(self):
        result = process_payment(order_id=1, number="1235")
        self.assertIsInstance(result, str)
        self.assertIn("чётным", result)

    def test_number_ending_with_zero_fails(self):
        result = process_payment(order_id=1, number="1230")
        self.assertIsInstance(result, str)
        self.assertIn("заканчиваться на 0", result)
