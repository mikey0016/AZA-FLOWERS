from django.contrib import admin
from apps.payments.models import Coupon, Payment, PaymentEvent, PaymentReceipt, PaymentSettings


class EventInline(admin.TabularInline):
    model = PaymentEvent
    extra = 0
    readonly_fields = ("kind", "amount", "by", "reason", "created_at")
    can_delete = False


class ReceiptInline(admin.TabularInline):
    model = PaymentReceipt
    extra = 0
    readonly_fields = ("file", "reference", "status", "uploaded_at", "reviewed_by",
                       "reviewed_at", "reject_reason")
    can_delete = False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "method", "required_amount", "received", "status", "updated_at")
    list_filter = ("method", "status")
    search_fields = ("order__no", "order__phone")
    readonly_fields = ("order", "method", "required_amount", "received", "status", "updated_at")
    inlines = [ReceiptInline, EventInline]

    def has_add_permission(self, request):
        return False


@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ("cardholder", "cash_advance_pct", "card_advance_pct", "updated_at")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "pct", "max_uses", "used", "active")
    list_editable = ("active",)


@admin.register(PaymentReceipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ("payment", "status", "uploaded_at", "reviewed_by")
    list_filter = ("status",)
    readonly_fields = ("payment", "file", "reference", "uploaded_at")
