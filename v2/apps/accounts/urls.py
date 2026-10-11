from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.accounts.views import AddressViewSet, LoginView, MeView, MyOrdersView, RegisterView

router = DefaultRouter()
router.register("addresses", AddressViewSet, basename="address")

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("my/orders/", MyOrdersView.as_view()),
    path("", include(router.urls)),
]
