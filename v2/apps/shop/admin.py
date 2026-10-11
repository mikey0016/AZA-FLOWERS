from django.contrib import admin
from apps.shop.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name_uz", "slug", "ordering")
    prepopulated_fields = {"slug": ("name_uz",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name_uz", "category", "price", "stock", "active", "featured")
    list_filter = ("category", "active", "featured")
    search_fields = ("name_uz", "slug")
    list_editable = ("price", "stock", "active")
