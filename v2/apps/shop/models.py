from django.db import models


class Category(models.Model):
    slug = models.SlugField(unique=True, max_length=60)
    name_uz = models.CharField(max_length=80)
    name_ru = models.CharField(max_length=80, blank=True, default="")
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordering", "name_uz"]
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self) -> str:
        return self.name_uz


class Product(models.Model):
    FEATURED_NONE = 0
    FEATURED_TOP = 1
    FEATURED_NEW = 2

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    slug = models.SlugField(unique=True, max_length=100)
    name_uz = models.CharField(max_length=120)
    name_ru = models.CharField(max_length=120, blank=True, default="")
    description_uz = models.TextField(blank=True, default="")
    description_ru = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=14, decimal_places=2)
    old_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    featured = models.PositiveSmallIntegerField(default=0)
    photo = models.ImageField(upload_to="products/%Y/%m/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-featured", "price"]
        indexes = [
            models.Index(fields=["category", "active"]),
            models.Index(fields=["active", "featured"]),
        ]
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"

    def __str__(self) -> str:
        return self.name_uz

    @property
    def discount_pct(self) -> int:
        if self.old_price and self.old_price > self.price:
            return round((self.old_price - self.price) / self.old_price * 100)
        return 0
