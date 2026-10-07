from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = "Профиль"
    verbose_name_plural = "Профиль"
    fields = ("phone", "avatar", "archived")


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = (
        "username", "email", "first_name", "last_name",
        "is_staff", "is_active", "archived_display",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "profile__archived")
    actions = ["archive_selected", "unarchive_selected"]

    def get_queryset(self, request):
        """Показываем всех, включая архивных."""
        return User.objects.all()

    def archived_display(self, obj):
        profile = getattr(obj, "profile", None)
        return bool(profile and profile.archived)
    archived_display.boolean = True
    archived_display.short_description = "Архивирован"

    @admin.action(description="Архивировать выбранных пользователей")
    def archive_selected(self, request, queryset):
        for user in queryset:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.archived = True
            profile.save(update_fields=["archived"])
            user.is_active = False
            user.save(update_fields=["is_active"])
        self.message_user(request, f"Архивировано пользователей: {queryset.count()}")

    @admin.action(description="Восстановить выбранных пользователей")
    def unarchive_selected(self, request, queryset):
        for user in queryset:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.archived = False
            profile.save(update_fields=["archived"])
            user.is_active = True
            user.save(update_fields=["is_active"])
        self.message_user(request, f"Восстановлено пользователей: {queryset.count()}")

    def delete_model(self, request, obj):
        """Вместо удаления — архивируем."""
        profile, _ = Profile.objects.get_or_create(user=obj)
        profile.archived = True
        profile.save(update_fields=["archived"])
        obj.is_active = False
        obj.save(update_fields=["is_active"])

    def delete_queryset(self, request, queryset):
        """Массовое «удаление» — архивируем."""
        Profile.objects.filter(user__in=queryset).update(archived=True)
        queryset.update(is_active=False)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "email_display", "archived")
    list_filter = ("archived",)
    search_fields = ("user__username", "user__email", "phone")
    actions = ["archive_selected", "unarchive_selected"]

    def email_display(self, obj):
        return obj.user.email

    email_display.short_description = "Email"
    email_display.admin_order_field = "user__email"

    @admin.action(description="Архивировать выбранные профили")
    def archive_selected(self, request, queryset):
        queryset.update(archived=True)
        # деактивируем связанных пользователей
        User.objects.filter(profile__in=queryset).update(is_active=False)
        self.message_user(request, f"Архивировано профилей: {queryset.count()}")

    @admin.action(description="Восстановить выбранные профили")
    def unarchive_selected(self, request, queryset):
        queryset.update(archived=False)
        User.objects.filter(profile__in=queryset).update(is_active=True)
        self.message_user(request, f"Восстановлено профилей: {queryset.count()}")
