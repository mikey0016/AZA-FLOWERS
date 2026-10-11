"""To'lov operatsiyalari: idempotent, tranzaksion, audit bilan."""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order
from apps.payments.models import Payment, PaymentEvent, money


class PaymentError(ValueError):
    pass


def _lock(payment_id: int) -> Payment:
    try:
        return Payment.objects.select_for_update().select_related("order").get(pk=payment_id)
    except Payment.DoesNotExist:
        raise PaymentError("To'lov topilmadi")


@transaction.atomic
def submit_receipt(payment_id: int, uploaded_file, reference: str = "") -> "PaymentReceipt":
    """Chek yuklash — HECH QACHON avtomatik to'langan deb belgilamaydi."""
    from apps.payments.models import PaymentReceipt
    p = _lock(payment_id)
    name = getattr(uploaded_file, "name", "")
    ext = (name.rsplit(".", 1)[-1] if "." in name else "").lower()
    if ext not in PaymentReceipt.ALLOWED_EXT:
        raise PaymentError("Faqat JPG/PNG/WEBP/PDF ruxsat etilgan")
    if uploaded_file.size > PaymentReceipt.MAX_SIZE:
        raise PaymentError("Fayl 8MB dan katta bo'lmasin")
    if p.status in (Payment.FULLY_PAID,):
        raise PaymentError("To'lov allaqachon yakunlangan")
    receipt = PaymentReceipt.objects.create(payment=p, file=uploaded_file, reference=reference or "")
    p.status = Payment.RECEIPT_SUBMITTED
    p.save(update_fields=["status", "updated_at"])
    PaymentEvent.objects.create(payment=p, kind="receipt_uploaded", by="customer")
    return receipt


@transaction.atomic
def confirm_advance(payment_id: int, amount, by: str = "") -> Payment:
    """Naqd 50% tasdiqlash. Ikki marta tasdiqlab bo'lmaydi (idempotent)."""
    p = _lock(payment_id)
    if p.status in (Payment.ADVANCE_CONFIRMED, Payment.PARTIALLY_PAID, Payment.FULLY_PAID):
        return p
    if p.method != Order.PAY_CASH:
        raise PaymentError("Bu karta to'lovi — advance emas")
    amount = money(amount)
    if amount <= 0 or amount != p.required_amount:
        raise PaymentError(f"Summa aynan {p.required_amount} bo'lishi shart")
    p.received = money(p.received + amount)
    p.status = Payment.ADVANCE_CONFIRMED
    p.save(update_fields=["received", "status", "updated_at"])
    PaymentEvent.objects.create(payment=p, kind="advance_confirmed", amount=amount, by=by)
    _sync_order_status(p, by)
    return p


@transaction.atomic
def confirm_card(payment_id: int, by: str = "") -> Payment:
    """Karta 100% tasdiqlash (faqat xodim)."""
    p = _lock(payment_id)
    if p.status == Payment.FULLY_PAID:
        return p
    if p.method != Order.PAY_CARD:
        raise PaymentError("Bu naqd to'lov")
    if p.status not in (Payment.AWAITING_CARD_VERIFY, Payment.RECEIPT_SUBMITTED, Payment.RECEIPT_REJECTED):
        raise PaymentError("Holat mos emas")
    p.received = money(p.order.total)
    p.status = Payment.FULLY_PAID
    p.save(update_fields=["received", "status", "updated_at"])
    PaymentEvent.objects.create(payment=p, kind="card_confirmed", amount=p.received, by=by)
    _sync_order_status(p, by)
    return p


@transaction.atomic
def reject_receipt(payment_id: int, reason: str, by: str = "") -> Payment:
    from apps.payments.models import PaymentReceipt
    p = _lock(payment_id)
    if p.status == Payment.FULLY_PAID:
        raise PaymentError("Yakunlangan to'lovni rad etib bo'lmaydi")
    if not reason.strip():
        raise PaymentError("Rad etish sababi shart")
    p.receipts.filter(status=PaymentReceipt.STATUS_PENDING).update(
        status=PaymentReceipt.STATUS_REJECTED, reviewed_by=by,
        reviewed_at=timezone.now(), reject_reason=reason[:300])
    p.status = Payment.RECEIPT_REJECTED
    p.save(update_fields=["status", "updated_at"])
    PaymentEvent.objects.create(payment=p, kind="receipt_rejected", by=by, reason=reason[:300])
    return p


@transaction.atomic
def record_cash(payment_id: int, amount, by: str = "") -> Payment:
    """Yetkazishda qolgan naqd pulni qayd etish."""
    p = _lock(payment_id)
    if p.method != Order.PAY_CASH:
        raise PaymentError("Faqat naqd buyurtmalar uchun")
    amount = money(amount)
    if amount <= 0:
        raise PaymentError("Summa noto'g'ri")
    p.received = money(p.received + amount)
    if p.received >= p.order.total:
        p.status = Payment.FULLY_PAID
    elif p.received > 0:
        p.status = Payment.PARTIALLY_PAID
    p.save(update_fields=["received", "status", "updated_at"])
    PaymentEvent.objects.create(payment=p, kind="cash_recorded", amount=amount, by=by)
    _sync_order_status(p, by)
    return p


def _sync_order_status(p: Payment, by: str) -> None:
    from apps.orders.services import set_order_status
    o = p.order
    try:
        if p.status == Payment.FULLY_PAID:
            for nxt in ("awaiting_verify", "confirmed"):
                if nxt in Order.TRANSITIONS.get(o.status, set()):
                    o = set_order_status(o, nxt, by)
        elif p.status in (Payment.ADVANCE_CONFIRMED, Payment.PARTIALLY_PAID):
            if Order.STATUS_AWAITING_VERIFY in Order.TRANSITIONS.get(o.status, set()):
                set_order_status(o, Order.STATUS_AWAITING_VERIFY, by)
    except Exception:
        pass
