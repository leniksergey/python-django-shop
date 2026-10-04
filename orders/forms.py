import datetime

from django import forms
from django.core.validators import RegexValidator

from catalog.models import Product

PHONE_RE = RegexValidator(
    regex=r"^\+?\d{10,15}$",
    message="Телефон должен содержать 10–15 цифр, допускается + в начале",
)


class CartItemForm(forms.Form):
    id = forms.IntegerField(min_value=1)
    count = forms.IntegerField(min_value=1, max_value=1000)


class OrderCreateForm(forms.Form):
    items = forms.JSONField()

    def clean_items(self):
        raw = self.cleaned_data["items"]
        if not isinstance(raw, list) or not raw:
            raise forms.ValidationError("Корзина пуста")

        parsed = []
        for idx, item in enumerate(raw):
            if not isinstance(item, dict):
                raise forms.ValidationError(f"Элемент #{idx} должен быть объектом")
            form = CartItemForm(item)
            if not form.is_valid():
                raise forms.ValidationError({f"item_{idx}": form.errors.as_json()})
            parsed.append(form.cleaned_data)

        merged = {}
        for item in parsed:
            merged[item["id"]] = merged.get(item["id"], 0) + item["count"]

        products = Product.objects.in_bulk(list(merged.keys()))
        missing = set(merged) - set(products)
        if missing:
            raise forms.ValidationError(f"Товары не найдены: {sorted(missing)}")

        for pid, product in products.items():
            if product.price is None or product.price <= 0:
                raise forms.ValidationError(f"Некорректная цена у товара {pid}")

        return [(products[pid], count) for pid, count in merged.items()]


class OrderUpdateForm(forms.Form):
    fullName = forms.CharField(max_length=200, min_length=1)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, validators=[PHONE_RE])
    deliveryType = forms.ChoiceField(choices=[("ordinary", "ordinary"), ("express", "express")])
    paymentType = forms.ChoiceField(choices=[("online", "online"), ("someone", "someone")])
    city = forms.CharField(max_length=100, min_length=1)
    address = forms.CharField(max_length=255, min_length=1)


class PaymentForm(forms.Form):
    """Валидация данных карты при оплате.

    Сумма НЕ принимается из формы — считаем из order.total_cost на бэке.
    """
    number = forms.CharField(min_length=13, max_length=25)
    name = forms.CharField(max_length=100, min_length=2, required=True)
    month = forms.IntegerField(min_value=1, max_value=12)
    year = forms.IntegerField(min_value=2000, max_value=2100)
    cvv = forms.CharField(min_length=3, max_length=3, required=True)

    def clean_number(self):
        raw = self.cleaned_data["number"]
        number = "".join(c for c in raw if c.isdigit())
        if not (13 <= len(number) <= 19):
            raise forms.ValidationError("Номер карты должен содержать 13–19 цифр")
        if not self._luhn_check(number):
            raise forms.ValidationError("Некорректный номер карты")
        return number

    def clean_name(self):
        name = (self.cleaned_data["name"] or "").strip()
        if len(name) < 2:
            raise forms.ValidationError("Укажите имя владельца карты")
        if not all(c.isalpha() or c in " .-" for c in name):
            raise forms.ValidationError(
                "Имя может содержать только буквы, пробел, точку и дефис"
            )
        return name

    def clean_cvv(self):
        cvv = self.cleaned_data["cvv"]
        if not cvv.isdigit():
            raise forms.ValidationError("CVV должен содержать только цифры")
        return cvv

    def clean_month(self):
        month = self.cleaned_data["month"]
        if not (1 <= month <= 12):
            raise forms.ValidationError("Месяц должен быть от 1 до 12")
        return month

    def clean_year(self):
        year = self.cleaned_data["year"]
        current = datetime.date.today().year
        if year < current:
            raise forms.ValidationError("Год не может быть меньше текущего")
        if year > current + 15:
            raise forms.ValidationError("Слишком далёкий год")
        return year

    def clean(self):
        cleaned = super().clean()
        month = cleaned.get("month")
        year = cleaned.get("year")
        if month and year:
            today = datetime.date.today()
            if (year, month) < (today.year, today.month):
                raise forms.ValidationError("Срок действия карты истёк")
        return cleaned

    def __init__(self, data=None, *args, **kwargs):
        if data is not None:
            data = dict(data)
            if "cvv" not in data and "code" in data:
                data["cvv"] = data["code"]
            for field in ("month", "year"):
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].strip() or None
        super().__init__(data, *args, **kwargs)

    @staticmethod
    def _luhn_check(number: str) -> bool:
        """Luhn — стандартный алгоритм проверки номера карты."""
        digits = [int(d) for d in number]
        checksum = 0
        parity = len(digits) % 2
        for i, d in enumerate(digits):
            if i % 2 == parity:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0
