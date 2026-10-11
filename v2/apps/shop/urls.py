from django.urls import path
from apps.shop.views import CategoryList, ProductDetail, ProductList

urlpatterns = [
    path("shop/categories/", CategoryList.as_view()),
    path("shop/products/", ProductList.as_view()),
    path("shop/products/<slug:slug>/", ProductDetail.as_view()),
]
