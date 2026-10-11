"""v1 (JSON) ma'lumotlarni v2 (Django) ga ko'chirish. Idempotent — qayta-qayta xavfsiz.

Ishlatish (repo ildizidan):
    py -3 v2/manage.py import_v1
"""
import json
import sys
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

V1 = Path(__file__).resolve().parent.parent.parent.parent.parent.parent


class Command(BaseCommand):
    help = "v1 JSON (products/orders/promos/payment) -> v2 DB"

    def handle(self, *args, **opts):
        sys.path.insert(0, str(V1))
        from app.seed import CATEGORIES, PRODUCTS

        from apps.orders.models import Order, OrderItem
        from apps.payments.models import Coupon, Payment, PaymentSettings, money
        from apps.shop.models import Category, Product

        with transaction.atomic():
            for i, c in enumerate(CATEGORIES):
                Category.objects.update_or_create(
                    slug=c["slug"], defaults={"name_uz": c["name"], "ordering": i})
            self.stdout.write(f"kategoriya: {len(CATEGORIES)}")
            n = 0
            for p in PRODUCTS:
                _, created = Product.objects.update_or_create(
                    slug=p["slug"],
                    defaults={
                        "category": Category.objects.get(slug=p["category"]),
                        "name_uz": p["name"],
                        "description_uz": p.get("description", ""),
                        "price": money(p["price"]),
                        "old_price": money(p["old_price"]) if p.get("old_price") else None,
                        "stock": p.get("stock", 0),
                        "active": True,
                        "featured": p.get("is_featured", 0),
                    })
                n += created
            self.stdout.write(f"mahsulot (yangi): {n}")

            try:
                orders = json.loads((V1 / "orders.json").read_text(encoding="utf-8"))
            except Exception:
                orders = []
            status_map = {"yangi": Order.STATUS_NEW, "qabul": Order.STATUS_CONFIRMED,
                          "awaiting_payment": Order.STATUS_AWAITING_PAYMENT,
                          "awaiting_confirm": Order.STATUS_AWAITING_VERIFY,
                          "accepted": Order.STATUS_CONFIRMED, "preparing": Order.STATUS_PREPARING,
                          "delivering": Order.STATUS_DELIVERING, "delivered": Order.STATUS_DELIVERED,
                          "closed": Order.STATUS_DELIVERED, "cancelled": Order.STATUS_CANCELLED,
                          "rejected": Order.STATUS_CANCELLED}
            m = 0
            for o in orders:
                if Order.objects.filter(no=o.get("no") or f"FAX-{o['id']}").exists():
                    continue
                total = money(o.get("total", 0))
                prepay = money(o.get("prepay", total // 2))
                method = Order.PAY_CARD if (o.get("pay") == "online") else Order.PAY_CASH
                order = Order.objects.create(
                    no=o.get("no") or f"FAX-{o['id']}", name=o.get("name", ""),
                    phone=o.get("phone", ""), address=o.get("address", "")[:200],
                    note=(o.get("note") or o.get("comment") or "")[:300],
                    lat=o.get("lat"), lon=o.get("lon"),
                    ship_method=Order.SHIP_EXPRESS if o.get("ship") == "express" else Order.SHIP_STANDARD,
                    ship_fee=money(o.get("ship_cost", 0)), pay_method=method,
                    subtotal=money(o.get("subtotal", total)),
                    discount=money(o.get("discount", 0)), total=total,
                    status=status_map.get(o.get("status", "yangi"), Order.STATUS_NEW),
                    tg_user=o.get("tg_user"))
                for ln in o.get("lines", []):
                    OrderItem.objects.create(order=order, product_slug=ln.get("slug", ""),
                                             name=ln.get("name", "")[:120],
                                             price=money(ln.get("price", 0)), qty=ln.get("qty", 1))
                Payment.objects.create(
                    order=order, method=method, required_amount=prepay,
                    received=Decimal("0"),
                    status=(Payment.AWAITING_CARD_VERIFY if method == Order.PAY_CARD
                            else Payment.AWAITING_ADVANCE))
                m += 1
            self.stdout.write(f"buyurtma (yangi): {m}")

            try:
                promos = json.loads((V1 / "promos.json").read_text(encoding="utf-8"))
            except Exception:
                promos = {}
            for code, p in promos.items():
                Coupon.objects.update_or_create(
                    code=code.upper(), defaults={"pct": p.get("pct", 0),
                                                 "max_uses": p.get("max_uses", 0),
                                                 "used": p.get("used", 0),
                                                 "active": bool(p.get("active", 1))})
            self.stdout.write(f"promokod: {len(promos)}")

            try:
                pay = json.loads((V1 / "payment.json").read_text(encoding="utf-8"))
                s = PaymentSettings.current()
                s.card_number = pay.get("pay_card", "")
                s.cash_advance_pct = pay.get("prepay_pct", 50)
                s.save()
                self.stdout.write("payment.json ko'chirildi")
            except Exception as e:
                self.stdout.write(f"payment.json: {e}")

        self.stdout.write(self.style.SUCCESS("Tayyor."))
