from decimal import Decimal
from django.db import models


class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_AWAITING_PAYMENT = "awaiting_payment"
    STATUS_AWAITING_VERIFY = "awaiting_verify"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PREPARING = "preparing"
    STATUS_READY = "ready"
    STATUS_DELIVERING = "delivering"
    STATUS_DELIVERED = "delivered"
    STATUS_CLOSED = "closed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_NEW, "Yangi"),
        (STATUS_AWAITING_PAYMENT, "To'lov kutilmoqda"),
        (STATUS_AWAITING_VERIFY, "Tekshiruv kutilmoqda"),
        (STATUS_CONFIRMED, "Tasdiqlangan"),
        (STATUS_PREPARING, "Tayyorlanmoqda"),
        (STATUS_READY, "Jo'natishga tayyor"),
        (STATUS_DELIVERING, "Yo'lda"),
        (STATUS_DELIVERED, "Yetkazildi"),
        (STATUS_CLOSED, "Yakunlandi"),
        (STATUS_CANCELLED, "Bekor qilindi"),
    ]

    # Ruxsat etilgan o'tishlar (controlled transitions)
    TRANSITIONS = {
        STATUS_NEW: {STATUS_AWAITING_PAYMENT, STATUS_CANCELLED},
        STATUS_AWAITING_PAYMENT: {STATUS_AWAITING_VERIFY, STATUS_CANCELLED},
        STATUS_AWAITING_VERIFY: {STATUS_CONFIRMED, STATUS_CANCELLED},
        STATUS_CONFIRMED: {STATUS_PREPARING, STATUS_CANCELLED},
        STATUS_PREPARING: {STATUS_READY, STATUS_CANCELLED},
        STATUS_READY: {STATUS_DELIVERING, STATUS_CANCELLED},
        STATUS_DELIVERING: {STATUS_DELIVERED, STATUS_CANCELLED},
        STATUS_DELIVERED: {STATUS_CLOSED},
        STATUS_CLOSED: set(),
        STATUS_CANCELLED: set(),
    }

    SHIP_STANDARD = "standard"
    SHIP_EXPRESS = "express"
    SHIP_CHOICES = [(SHIP_STANDARD, "Standart"), (SHIP_EXPRESS, "Tezkor")]

    PAY_CASH = "cash"
    PAY_CARD = "card"
    PAY_CHOICES = [(PAY_CASH, "Naqd (50/50)"), (PAY_CARD, "Karta (100%)")]

    no = models.CharField(max_length=20, unique=True)
    client_key = models.CharField(max_length=64, unique=True, null=True, blank=True,
                                  help_text="Takroriy yuborishdan himoya (idempotentlik kaliti)")
    name = models.CharField(max_length=80)
    phone = models.CharField(max_length=20)
    region = models.CharField(max_length=60, blank=True, default="")
    city = models.CharField(max_length=60, blank=True, default="")
    address = models.CharField(max_length=200, blank=True, default="")
    note = models.CharField(max_length=300, blank=True, default="")
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    ship_method = models.CharField(max_length=20, choices=SHIP_CHOICES, default=SHIP_STANDARD)
    ship_fee = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    pay_method = models.CharField(max_length=20, choices=PAY_CHOICES, default=PAY_CASH)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_NEW)
    tg_user = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["status", "-id"]),
            models.Index(fields=["phone"]),
        ]
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"

    def __str__(self) -> str:
        return f"{self.no} · {self.name}"


class OrderItem(models.Model):
    """Narx/nom snapshot — mahsulot yangilansa ham tarix to'g'ri qoladi."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_slug = models.CharField(max_length=100)
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=14, decimal_places=2)
    qty = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Buyurtma tarkibi"
        verbose_name_plural = "Buyurtma tarkibi"

    @property
    def line_total(self) -> Decimal:
        return self.price * self.qty


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=24)
    to_status = models.CharField(max_length=24)
    by = models.CharField(max_length=80, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Holat tarixi"
        verbose_name_plural = "Holat tarixi"
