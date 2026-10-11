from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.orders.views import OrderViewSet, PublicOrderCreate, PublicOrderTrack

router = DefaultRouter()
router.register("staff/orders", OrderViewSet, basename="staff-order")

urlpatterns = [
    path("orders/", PublicOrderCreate.as_view()),
    path("orders/<int:pk>/", PublicOrderTrack.as_view()),
    path("", include(router.urls)),
]
