"""Akkaunt testlari: ro'yxat, kirish, profil, manzil, mening buyurtmalarim."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.accounts.models import Address, CustomerProfile
from apps.orders.services import create_order
from apps.shop.models import Category, Product
from decimal import Decimal


def mkproduct():
    cat, _ = Category.objects.get_or_create(slug="t", defaults={"name_uz": "T"})
    return Product.objects.create(category=cat, slug="g1", name_uz="Gul",
                                  price=Decimal("100000"), stock=10)


class AccountsTest(TestCase):
    def test_register_login_me(self):
        c = APIClient()
        r = c.post("/api/v2/auth/register/",
                   {"name": "Ali Vali", "phone": "+998 90 111 22 33", "password": "pass1234"},
                   format="json")
        self.assertEqual(r.status_code, 201)
        self.assertIn("token", r.data)
        self.assertEqual(r.data["user"]["phone"], "998901112233")
        # Qayta ro'yxat — band
        r2 = c.post("/api/v2/auth/register/",
                    {"name": "Ali", "phone": "998901112233", "password": "pass1234"},
                    format="json")
        self.assertEqual(r2.status_code, 400)
        # Login
        r3 = c.post("/api/v2/auth/login/",
                    {"phone": "+998901112233", "password": "pass1234"}, format="json")
        self.assertEqual(r3.status_code, 200)
        # Noto'g'ri parol
        r4 = c.post("/api/v2/auth/login/",
                    {"phone": "998901112233", "password": "xxx"}, format="json")
        self.assertEqual(r4.status_code, 400)
        # Me
        c.credentials(HTTP_AUTHORIZATION="Token " + r3.data["token"])
        me = c.get("/api/v2/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["name"], "Ali Vali")
        # Anonim kira olmaydi
        anon = APIClient().get("/api/v2/auth/me/")
        self.assertIn(anon.status_code, (401, 403))

    def test_addresses(self):
        u = User.objects.create_user("998900000001", password="pass1234")
        CustomerProfile.objects.create(user=u, name="U", phone="998900000001")
        c = APIClient()
        c.force_authenticate(user=u)
        r = c.post("/api/v2/addresses/",
                   {"label": "Uy", "region": "Toshkent shahri", "city": "Chilonzor",
                    "address": "12-uy", "is_default": True}, format="json")
        self.assertEqual(r.status_code, 201)
        r2 = c.post("/api/v2/addresses/",
                    {"label": "Ish", "city": "Yunusobod", "address": "5-uy",
                     "is_default": True}, format="json")
        self.assertEqual(r2.status_code, 201)
        dflt = Address.objects.filter(user=u, is_default=True)
        self.assertEqual(dflt.count(), 1)
        self.assertEqual(dflt.first().label, "Ish")
        # Boshqa user ko'rmaydi
        u2 = User.objects.create_user("998900000002", password="pass1234")
        CustomerProfile.objects.create(user=u2, name="U2", phone="998900000002")
        c2 = APIClient()
        c2.force_authenticate(user=u2)
        self.assertEqual(c2.get("/api/v2/addresses/").data, [])

    def test_my_orders(self):
        p = mkproduct()
        create_order({"name": "Ali", "phone": "+998901112233", "city": "Toshkent",
                      "address": "Manzil 12345", "items": [{"slug": p.slug, "qty": 1}]})
        u = User.objects.create_user("998901112233", password="pass1234")
        CustomerProfile.objects.create(user=u, name="Ali", phone="998901112233")
        c = APIClient()
        c.force_authenticate(user=u)
        r = c.get("/api/v2/my/orders/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]["name"], "Ali")
