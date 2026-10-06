from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderItem
from .delivery import DeliverySettings


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "price", "count")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "created_at", "full_name", "phone",
        "delivery_type", "payment_type", "total_cost_display",
        "status_colored", "archived",
    )
    list_filter = ("status", "delivery_type", "payment_type", "archived", "created_at")
    search_fields = ("id", "full_name", "phone", "email")
    readonly_fields = ("created_at",)
    inlines = [OrderItemInline]
    actions = ["archive_selected", "unarchive_selected"]

    fieldsets = (
        ("Основное", {
            "fields": ("user", "status", "created_at", "archived")
        }),
        ("Покупатель", {
            "fields": ("full_name", "email", "phone")
        }),
        ("Доставка", {
            "fields": ("delivery_type", "city", "address", "comment")
        }),
        ("Оплата", {
            "fields": ("payment_type", "payment_error")
        }),
    )

    def total_cost_display(self, obj):
        return f"{obj.total_cost} ₽"
    total_cost_display.short_description = "Итого"

    def status_colored(self, obj):
        colors = {
            "new": "gray",
            "accepted": "orange",
            "paid": "green",
            "failed": "red",
        }
        color = colors.get(obj.status, "black")
        return format_html(
            '<b style="color: {};">{}</b>',
            color,
            obj.get_status_display(),
        )
    status_colored.short_description = "Статус"

    # --- Мягкое удаление ---

    def get_queryset(self, request):
        """Показываем в админке и архивные заказы."""
        return Order.all_objects.get_queryset()

    @admin.action(description="Архивировать выбранные заказы")
    def archive_selected(self, request, queryset):
        updated = queryset.update(archived=True)
        self.message_user(request, f"Архивировано заказов: {updated}")

    @admin.action(description="Восстановить выбранные заказы")
    def unarchive_selected(self, request, queryset):
        updated = queryset.update(archived=False)
        self.message_user(request, f"Восстановлено заказов: {updated}")

    def delete_model(self, request, obj):
        """Вместо удаления — архивируем."""
        obj.archived = True
        obj.save(update_fields=["archived"])

    def delete_queryset(self, request, queryset):
        """Массовое «удаление» — архивируем."""
        queryset.update(archived=True)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "price", "count")
    search_fields = ("order__id", "product__title")


@admin.register(DeliverySettings)
class DeliverySettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not DeliverySettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
