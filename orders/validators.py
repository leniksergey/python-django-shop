from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r"^\+?\d{10,15}$",
    message=(
        "Телефон должен содержать 10–15 цифр. "
        "Допускается только '+' в начале."
    ),
)
