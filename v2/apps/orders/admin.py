from django.contrib import admin
from apps.orders.models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_slug", "name", "price", "qty")


class HistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("from_status", "to_status", "by", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("no", "name", "phone", "total", "status", "pay_method", "created_at")
    list_filter = ("status", "pay_method", "ship_method")
    search_fields = ("no", "phone", "name")
    readonly_fields = ("no", "subtotal", "discount", "total", "created_at", "updated_at")
    inlines = [OrderItemInline, HistoryInline]
