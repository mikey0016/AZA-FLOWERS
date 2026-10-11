from rest_framework import generics, permissions, viewsets
from apps.shop.models import Category, Product
from apps.shop.serializers import CategorySerializer, ProductSerializer


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ProductList(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Product.objects.filter(active=True).select_related("category")
        p = self.request.query_params
        if p.get("category") and p["category"] != "all":
            qs = qs.filter(category__slug=p["category"])
        if p.get("q"):
            qs = qs.filter(name_uz__icontains=p["q"])
        if p.get("featured") == "1":
            qs = qs.exclude(featured=0)
        sort = p.get("sort", "popular")
        if sort == "cheap":
            qs = qs.order_by("price")
        elif sort == "expensive":
            qs = qs.order_by("-price")
        elif sort == "new":
            qs = qs.order_by("-created_at")
        elif sort == "discount":
            qs = sorted(qs, key=lambda x: -x.discount_pct)
        return qs


class ProductDetail(generics.RetrieveAPIView):
    queryset = Product.objects.filter(active=True).select_related("category")
    serializer_class = ProductSerializer
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]


class StaffProductViewSet(viewsets.ModelViewSet):
    """Xodimlar uchun to'liq CRUD (bot ham shundan foydalanadi)."""
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = "slug"
