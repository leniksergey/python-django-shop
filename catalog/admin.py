from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "parent", "image_preview", "archived")
    list_filter = ("archived",)
    search_fields = ("title",)
    actions = ["archive", "unarchive"]

    def get_queryset(self, request):
        return Category.all_objects.all()

    def get_deleted_objects(self, objs, request):
        return [str(obj) for obj in objs], {self.model._meta.verbose_name_plural: len(objs)}, set(), []

    def delete_model(self, request, obj):
        obj.archived = True
        obj.save()

    def delete_queryset(self, request, queryset):
        queryset.update(archived=True)

    @admin.action(description="Archive selected categories")
    def archive(self, request, queryset):
        queryset.update(archived=True)

    @admin.action(description="Unarchive selected categories")
    def unarchive(self, request, queryset):
        queryset.update(archived=False)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "No icon"
    image_preview.short_description = "Icon"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "price", "count", "archived")
    list_filter = ("category", "archived")
    search_fields = ("title",)
    inlines = [ProductImageInline]
    actions = ["archive", "unarchive"]

    def get_queryset(self, request):
        return Product.all_objects.all()

    def get_deleted_objects(self, objs, request):
        return [str(obj) for obj in objs], {self.model._meta.verbose_name_plural: len(objs)}, set(), []

    def delete_model(self, request, obj):
        obj.archived = True
        obj.save()

    def delete_queryset(self, request, queryset):
        queryset.update(archived=True)

    @admin.action(description="Archive selected products")
    def archive(self, request, queryset):
        queryset.update(archived=True)

    @admin.action(description="Unarchive selected products")
    def unarchive(self, request, queryset):
        queryset.update(archived=False)
