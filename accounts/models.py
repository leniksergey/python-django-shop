from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models

PHONE_RE = RegexValidator(
    regex=r"^\+?\d{10,15}$",
    message="Телефон должен содержать 10–15 цифр, допускается + в начале",
)


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    phone = models.CharField(
        max_length=32,
        blank=True,
        validators=[PHONE_RE],
        verbose_name="Телефон",
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        verbose_name="Аватар",
    )
    archived = models.BooleanField(default=False, verbose_name="Архивирован")

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return self.user.username
