from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.orders.views import (
    BotLinkView, BotPendingView, GeoReverseView, OrderViewSet,
    PublicOrderCreate, PublicOrderTrack,
)

router = DefaultRouter()
router.register("staff/orders", OrderViewSet, basename="staff-order")

urlpatterns = [
    path("orders/", PublicOrderCreate.as_view()),
    path("orders/<int:pk>/", PublicOrderTrack.as_view()),
    path("geo/reverse/", GeoReverseView.as_view()),
    path("staff/bot/pending/", BotPendingView.as_view()),
    path("staff/bot/link/", BotLinkView.as_view()),
    path("", include(router.urls)),
]
