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
    deliveryType = forms.ChoiceField(
        choices=[("ordinary", "ordinary"), ("express", "express")]
    )
    paymentType = forms.ChoiceField(
        choices=[("online", "online"), ("someone", "someone")]
    )
    city = forms.CharField(max_length=100, min_length=1)
    address = forms.CharField(max_length=255, min_length=1)
    comment = forms.CharField(max_length=1000, required=False)


class PaymentForm(forms.Form):
    """Форма фиктивной оплаты.

    Валидация по ТЗ: номер — только цифры, не длиннее 8 символов, чётный.
    Одно поле используется для обоих способов оплаты:
    «Онлайн картой» и «С чужого счёта».
    """

    number = forms.CharField(min_length=1, max_length=8)

    def clean_number(self):
        number = self.cleaned_data["number"].strip()
        if not number.isdigit():
            raise forms.ValidationError("Номер должен содержать только цифры")
        if len(number) > 8:
            raise forms.ValidationError("Номер не может быть длиннее 8 цифр")
        if int(number) % 2 != 0:
            raise forms.ValidationError("Номер должен быть чётным")
        return number
