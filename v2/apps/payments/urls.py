from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.payments.views import CouponViewSet, PaymentSettingsView, PaymentViewSet, ReceiptUpload

router = DefaultRouter()
router.register("staff/payments", PaymentViewSet, basename="staff-payment")
router.register("staff/coupons", CouponViewSet, basename="staff-coupon")

urlpatterns = [
    path("staff/payment-settings/", PaymentSettingsView.as_view()),
    path("receipts/", ReceiptUpload.as_view()),
    path("", include(router.urls)),
]
