from django.contrib import admin
from apps.accounts.models import Address, CustomerProfile


@admin.register(CustomerProfile)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "user")
    search_fields = ("name", "phone")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "city", "is_default")
    list_filter = ("is_default",)
    search_fields = ("city", "address")
