from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "FAX Flores — admin"
admin.site.site_title = "FAX Flores"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v2/", include([
        path("", include("apps.shop.urls")),
        path("", include("apps.orders.urls")),
        path("", include("apps.payments.urls")),
    ])),
]
