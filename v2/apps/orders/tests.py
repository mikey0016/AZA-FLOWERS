"""Buyurtma + to'lov oqimi testlari: yaratish, holatlar, chek, audit, ruxsatlar."""
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.orders.models import Order
from apps.orders.services import OrderError, create_order, set_order_status
from apps.payments.models import Coupon, Payment
from apps.payments.services import (
    PaymentError, confirm_advance, confirm_card, record_cash, reject_receipt, submit_receipt,
)
from apps.shop.models import Category, Product


def mkproduct(slug="atirgul-25", price="100000", stock=10):
    cat, _ = Category.objects.get_or_create(slug="test", defaults={"name_uz": "Test"})
    return Product.objects.create(category=cat, slug=slug, name_uz="Test Gul",
                                  price=Decimal(price), stock=stock)


def mkorder(**kw):
    p = kw.pop("product", None) or mkproduct()
    d = {"name": "Ali", "phone": "998901234567", "city": "Toshkent",
         "address": "Chilonzor 12", "items": [{"slug": p.slug, "qty": 1}]}
    d.update(kw)
    return create_order(d)


class OrderFlowTest(TestCase):
    def test_totals_server_side(self):
        p = mkproduct()
        o = mkorder(product=p, items=[{"slug": p.slug, "qty": 2}])
        self.assertEqual(o.subtotal, Decimal("200000"))
        self.assertEqual(o.total, Decimal("200000"))
        self.assertEqual(o.payment.required_amount, Decimal("100000"))
        self.assertEqual(o.status, Order.STATUS_AWAITING_PAYMENT)

    def test_stock_validation(self):
        p = mkproduct(stock=1)
        with self.assertRaises(OrderError):
            mkorder(product=p, items=[{"slug": p.slug, "qty": 5}])

    def test_unknown_product(self):
        with self.assertRaises(OrderError):
            mkorder(items=[{"slug": "yoq-narsa", "qty": 1}])

    def test_idempotency(self):
        p = mkproduct()
        kw = {"product": p, "client_key": "k-123"}
        o1 = mkorder(**kw)
        o2 = mkorder(**kw)
        self.assertEqual(o1.pk, o2.pk)
        self.assertEqual(Order.objects.filter(client_key="k-123").count(), 1)

    def test_coupon(self):
        Coupon.objects.create(code="TEST10", pct=10)
        o = mkorder(promo="test10")
        self.assertEqual(o.discount, Decimal("10000"))
        self.assertEqual(o.total, Decimal("90000"))
        self.assertEqual(o.payment.required_amount, Decimal("45000"))

    def test_bad_coupon(self):
        with self.assertRaises(OrderError):
            mkorder(promo="YOQ")

    def test_transition_rules(self):
        o = mkorder()
        with self.assertRaises(OrderError):
            set_order_status(o, Order.STATUS_DELIVERED)
        o = set_order_status(o, Order.STATUS_AWAITING_VERIFY)
        self.assertEqual(o.status, Order.STATUS_AWAITING_VERIFY)
        self.assertEqual(o.history.count(), 2)

    def test_stock_decrement_on_prepare(self):
        p = mkproduct(stock=3)
        o = mkorder(product=p, items=[{"slug": p.slug, "qty": 2}])
        set_order_status(o, Order.STATUS_AWAITING_VERIFY)
        set_order_status(o, Order.STATUS_CONFIRMED)
        set_order_status(o, Order.STATUS_PREPARING)
        p.refresh_from_db()
        self.assertEqual(p.stock, 1)


class PaymentFlowTest(TestCase):
    def test_cash_advance_and_rest(self):
        o = mkorder()
        p = o.payment
        confirm_advance(p.pk, Decimal("50000"), by="admin")
        p.refresh_from_db()
        self.assertEqual(p.status, Payment.ADVANCE_CONFIRMED)
        self.assertEqual(p.remaining, Decimal("50000"))
        # Ikkinchi tasdiq — idempotent, xatosiz qaytadi
        confirm_advance(p.pk, Decimal("50000"), by="admin")
        record_cash(p.pk, Decimal("50000"), by="kuryer")
        p.refresh_from_db()
        self.assertEqual(p.status, Payment.FULLY_PAID)
        self.assertEqual(p.events.count(), 3)  # created + advance + cash

    def test_advance_wrong_amount(self):
        o = mkorder()
        with self.assertRaises(PaymentError):
            confirm_advance(o.payment.pk, Decimal("99999"), by="admin")

    def test_card_full(self):
        o = mkorder(pay="card")
        p = o.payment
        self.assertEqual(p.required_amount, Decimal("100000"))
        self.assertEqual(p.status, Payment.AWAITING_CARD_VERIFY)
        confirm_card(p.pk, by="admin")
        p.refresh_from_db()
        self.assertEqual(p.status, Payment.FULLY_PAID)
        self.assertEqual(p.remaining, Decimal("0"))

    def test_receipt_never_autopays(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        o = mkorder()
        f = SimpleUploadedFile("chek.jpg", b"\xff\xd8fake", content_type="image/jpeg")
        r = submit_receipt(o.payment.pk, f)
        self.assertEqual(r.status, "pending")
        o.payment.refresh_from_db()
        self.assertNotEqual(o.payment.status, Payment.FULLY_PAID)

    def test_receipt_validation(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        o = mkorder()
        bad = SimpleUploadedFile("x.exe", b"MZ", content_type="application/octet-stream")
        with self.assertRaises(PaymentError):
            submit_receipt(o.payment.pk, bad)

    def test_reject_and_resubmit(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        o = mkorder()
        f = SimpleUploadedFile("a.jpg", b"\xff\xd8", content_type="image/jpeg")
        submit_receipt(o.payment.pk, f)
        reject_receipt(o.payment.pk, "Xira tushgan", by="admin")
        o.payment.refresh_from_db()
        self.assertEqual(o.payment.status, Payment.RECEIPT_REJECTED)
        f2 = SimpleUploadedFile("b.jpg", b"\xff\xd8", content_type="image/jpeg")
        r2 = submit_receipt(o.payment.pk, f2)
        self.assertEqual(r2.status, "pending")

    def test_reject_needs_reason(self):
        o = mkorder()
        with self.assertRaises(PaymentError):
            reject_receipt(o.payment.pk, "  ", by="admin")

    def test_unauthorized_api(self):
        c = APIClient()
        r = c.get("/api/v2/staff/orders/")
        self.assertEqual(r.status_code, 403)
        r = c.get("/api/v2/staff/payments/")
        self.assertEqual(r.status_code, 403)

    def test_staff_api(self):
        User.objects.create_superuser("admin", "a@a.uz", "pass12345")
        c = APIClient()
        c.force_authenticate(user=User.objects.get(username="admin"))
        r = c.get("/api/v2/staff/orders/")
        self.assertEqual(r.status_code, 200)
        # Oddiy user (staff emas) kira olmaydi
        User.objects.create_user("u", "u@u.uz", "pass12345")
        c2 = APIClient()
        c2.force_authenticate(user=User.objects.get(username="u"))
        self.assertEqual(c2.get("/api/v2/staff/orders/").status_code, 403)

    def test_public_create_and_track(self):
        p = mkproduct()
        c = APIClient()
        r = c.post("/api/v2/orders/", {"name": "Ali", "phone": "998901234567",
                                       "city": "Toshkent", "address": "Chilonzor 12",
                                       "items": [{"slug": p.slug, "qty": 1}]}, format="json")
        self.assertEqual(r.status_code, 201)
        oid = r.data["id"]
        ok = c.get(f"/api/v2/orders/{oid}/?phone=998901234567")
        self.assertEqual(ok.status_code, 200)
        bad = c.get(f"/api/v2/orders/{oid}/?phone=998900000000")
        self.assertEqual(bad.status_code, 403)
