"""Buyurtma yaratish: narxlar backend'da qayta hisoblanadi, zaxira tekshiriladi."""
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.orders.models import Order, OrderItem, OrderStatusHistory
from apps.payments.models import (
    Coupon, Payment, PaymentEvent, PaymentSettings, money, split_payment,
)
from apps.shop.models import Product

SHIP_FEES = {"standard": Decimal("0"), "express": Decimal("30000")}


class OrderError(ValueError):
    pass


def _gen_no() -> str:
    stamp = int(timezone.now().timestamp() * 1000) % 1000000
    return f"AZA-{stamp:06d}"


@transaction.atomic
def create_order(data: dict, by: str = "site") -> Order:
    items = data.get("items") or []
    if not items:
        raise OrderError("Savat bo'sh")
    name = (data.get("name") or "").strip()
    phone = "".join(ch for ch in str(data.get("phone") or "") if ch.isdigit())
    if len(name) < 2:
        raise OrderError("Ism kiritilmadi")
    if len(phone) < 9:
        raise OrderError("Telefon noto'g'ri")
    if len((data.get("city") or "").strip()) < 2:
        raise OrderError("Shahar kiritilmadi")
    address = (data.get("address") or "").strip()
    if len(address) < 5 and not (data.get("lat") and data.get("lon")):
        raise OrderError("Manzil kiritilmadi")

    # Idempotentlik: bir xil kalit ikki marta kelmasin
    client_key = (data.get("client_key") or "").strip() or None
    if client_key:
        existing = Order.objects.filter(client_key=client_key).first()
        if existing:
            return existing

    ship_method = data.get("ship") if data.get("ship") in SHIP_FEES else Order.SHIP_STANDARD
    pay_method = data.get("pay") if data.get("pay") in (Order.PAY_CASH, Order.PAY_CARD) else Order.PAY_CASH
    ship_fee = SHIP_FEES[ship_method]

    lines = []
    subtotal = Decimal("0")
    slugs = [it.get("slug") for it in items]
    products = {p.slug: p for p in Product.objects.select_for_update().filter(slug__in=slugs, active=True)}
    for it in items:
        qty = max(1, min(50, int(it.get("qty", 1))))
        p = products.get(it.get("slug"))
        if not p:
            raise OrderError(f"Noma'lum mahsulot: {it.get('slug')}")
        if qty > p.stock:
            raise OrderError(f"«{p.name_uz}» dan faqat {p.stock} dona qoldi")
        lines.append((p, qty))
        subtotal += money(p.price) * qty

    discount = Decimal("0")
    promo_code = (data.get("promo") or "").strip().upper()
    if promo_code:
        try:
            coupon = Coupon.objects.get(code=promo_code, active=True)
        except Coupon.DoesNotExist:
            raise OrderError("Bunday promokod yo'q")
        if coupon.max_uses and coupon.used >= coupon.max_uses:
            raise OrderError("Promokod tugagan")
        discount = money(subtotal * coupon.pct / 100)

    total = money(subtotal - discount + ship_fee)
    settings = PaymentSettings.current()
    advance, _rest = split_payment(total, "card" if pay_method == Order.PAY_CARD else "cash",
                                   settings.cash_advance_pct)

    order = Order.objects.create(
        no=_gen_no(), client_key=client_key,
        name=name, phone=phone,
        region=(data.get("region") or "")[:60], city=(data.get("city") or "")[:60],
        address=address[:200], note=(data.get("note") or "")[:300],
        lat=data.get("lat"), lon=data.get("lon"),
        ship_method=ship_method, ship_fee=ship_fee, pay_method=pay_method,
        subtotal=subtotal, discount=discount, total=total,
        status=Order.STATUS_AWAITING_PAYMENT,
        tg_user=data.get("tg_user"),
    )
    for p, qty in lines:
        OrderItem.objects.create(order=order, product_slug=p.slug,
                                 name=p.name_uz, price=money(p.price), qty=qty)
    OrderStatusHistory.objects.create(order=order, from_status="", to_status=order.status, by=by)
    Payment.objects.create(
        order=order, method=pay_method, required_amount=advance,
        status=(Payment.AWAITING_CARD_VERIFY if pay_method == Order.PAY_CARD
                else Payment.AWAITING_ADVANCE),
    )
    PaymentEvent.objects.create(payment=order.payment, kind="order_created",
                                amount=total, by=by)
    if promo_code:
        Coupon.objects.filter(code=promo_code).update(used=F("used") + 1)
    return order


@transaction.atomic
def set_order_status(order: Order, to_status: str, by: str = "") -> Order:
    allowed = Order.TRANSITIONS.get(order.status, set())
    if to_status not in allowed:
        raise OrderError(f"Holat o'tishi mumkin emas: {order.status} → {to_status}")
    prev = order.status
    if to_status == Order.STATUS_PREPARING:
        # Zaxirani atomar kamaytirish (oversell himoyasi)
        for item in order.items.select_related("order").all():
            updated = Product.objects.filter(
                slug=item.product_slug, stock__gte=item.qty).update(
                stock=F("stock") - item.qty)
            if not updated:
                raise OrderError(f"Zaxira yetarli emas: {item.name}")
    order.status = to_status
    order.save(update_fields=["status", "updated_at"])
    OrderStatusHistory.objects.create(order=order,
                                      from_status=prev, to_status=to_status, by=by)
    return order
