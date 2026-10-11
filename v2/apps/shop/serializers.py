from rest_framework import serializers
from apps.shop.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "slug", "name_uz", "name_ru"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_slug = serializers.SlugRelatedField(
        source="category", slug_field="slug",
        queryset=Category.objects.all(), write_only=True, required=False)
    discount_pct = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ["id", "slug", "name_uz", "name_ru", "category", "category_slug",
                  "price", "old_price", "discount_pct", "stock", "active",
                  "featured", "description_uz", "photo"]
