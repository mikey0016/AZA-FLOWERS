"""Qo'lda to'lov tizimi: Naqd 50/50, Karta 100%. Barcha harakatlar event sifatida."""
from decimal import Decimal, ROUND_HALF_UP
from django.db import models


def money(v) -> Decimal:
    return Decimal(str(v)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def split_payment(total: Decimal, pay_method: str, cash_pct: int = 50) -> tuple[Decimal, Decimal]:
    """(advance, remaining). advance+remaining har doim total ga teng."""
    total = money(total)
    if pay_method == "card":
        return total, Decimal("0")
    advance = (total * cash_pct / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return advance, total - advance


class PaymentSettings(models.Model):
    """Yagona sozlamalar qatori (admin paneldan tahrirlanadi)."""
    cardholder = models.CharField(max_length=80, blank=True, default="")
    card_number = models.CharField(max_length=24, blank=True, default="")
    instructions_uz = models.TextField(blank=True, default="")
    instructions_ru = models.TextField(blank=True, default="")
    cash_enabled = models.BooleanField(default=True)
    cash_advance_pct = models.PositiveSmallIntegerField(default=50)
    card_advance_pct = models.PositiveSmallIntegerField(default=100)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "To'lov sozlamasi"
        verbose_name_plural = "To'lov sozlamalari"

    def __str__(self) -> str:
        return "To'lov sozlamalari"

    @classmethod
    def current(cls) -> "PaymentSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Payment(models.Model):
    AWAITING_ADVANCE = "awaiting_advance_payment"
    AWAITING_CARD_VERIFY = "awaiting_card_payment_verification"
    RECEIPT_SUBMITTED = "receipt_submitted"
    ADVANCE_CONFIRMED = "advance_payment_confirmed"
    PARTIALLY_PAID = "partially_paid"
    RECEIPT_REJECTED = "receipt_rejected"
    FULLY_PAID = "fully_paid"
    REFUND_PENDING = "refund_pending"
    REFUNDED = "refunded"

    STATUS_CHOICES = [
        (AWAITING_ADVANCE, "Oldindan to'lov kutilmoqda"),
        (AWAITING_CARD_VERIFY, "Karta to'lovi tekshiruvi"),
        (RECEIPT_SUBMITTED, "Chek yuborilgan"),
        (ADVANCE_CONFIRMED, "Oldindan to'lov tasdiqlangan"),
        (PARTIALLY_PAID, "Qisman to'langan"),
        (RECEIPT_REJECTED, "Chek rad etilgan"),
        (FULLY_PAID, "To'liq to'langan"),
        (REFUND_PENDING, "Qaytarish kutilmoqda"),
        (REFUNDED, "Qaytarilgan"),
    ]

    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=20)
    required_amount = models.DecimalField(max_digits=14, decimal_places=2,
                                          help_text="Hozir to'lanishi shart (advance)")
    received = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    status = models.CharField(max_length=40, choices=STATUS_CHOICES)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"

    def __str__(self) -> str:
        return f"{self.order.no} · {self.get_status_display()}"

    @property
    def remaining(self) -> Decimal:
        return money(self.order.total - self.received)


class PaymentEvent(models.Model):
    """Har bir moliyaviy harakat — kim, qachon, nima o'zgardi (audit)."""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="events")
    kind = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    by = models.CharField(max_length=80, default="", blank=True)
    reason = models.CharField(max_length=300, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "To'lov hodisasi"
        verbose_name_plural = "To'lov tarixi (audit)"

    def __str__(self) -> str:
        return f"{self.payment.order.no} · {self.kind} · {self.amount}"


def receipt_upload_to(instance, filename: str) -> str:
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "bin")[:10]
    safe = "".join(ch for ch in filename.rsplit(".", 1)[0] if ch.isalnum() or ch in ("-", "_"))[:40] or "chek"
    return f"receipts/{instance.payment.order.no}/{safe}.{ext.lower()}"


class PaymentReceipt(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Tekshiruvda"),
        (STATUS_ACCEPTED, "Qabul qilingan"),
        (STATUS_REJECTED, "Rad etilgan"),
    ]
    ALLOWED_EXT = {"jpg", "jpeg", "png", "webp", "pdf"}
    MAX_SIZE = 8 * 1024 * 1024

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="receipts")
    file = models.FileField(upload_to=receipt_upload_to)
    reference = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.CharField(max_length=80, blank=True, default="")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reject_reason = models.CharField(max_length=300, blank=True, default="")

    class Meta:
        ordering = ["-id"]
        verbose_name = "Chek"
        verbose_name_plural = "Cheklar"

    def __str__(self) -> str:
        return f"{self.payment.order.no} · {self.get_status_display()}"


class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    pct = models.PositiveSmallIntegerField()
    max_uses = models.PositiveIntegerField(default=0, help_text="0 = cheksiz")
    used = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Promokod"
        verbose_name_plural = "Promokodlar"

    def __str__(self) -> str:
        return f"{self.code} — {self.pct}%"
