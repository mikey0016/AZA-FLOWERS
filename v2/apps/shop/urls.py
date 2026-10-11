from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.shop.views import CategoryList, ProductDetail, ProductList, StaffProductViewSet

router = DefaultRouter()
router.register("staff/products", StaffProductViewSet, basename="staff-product")

urlpatterns = [
    path("shop/categories/", CategoryList.as_view()),
    path("shop/products/", ProductList.as_view()),
    path("shop/products/<slug:slug>/", ProductDetail.as_view()),
    path("", include(router.urls)),
]
