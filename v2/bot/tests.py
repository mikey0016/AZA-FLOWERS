"""v2 bot sof funksiya testlari (tarmoq kerak emas)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bot as B
from texts import order_keyboard, order_text, payment_instructions, st_label, user_status_text


def mkorder(**kw):
    o = {"id": 5, "no": "FAX-000005", "name": "Ali", "phone": "9981",
         "region": "Toshkent shahri", "city": "Chilonzor", "address": "12-uy",
         "note": "", "ship_method": "standard", "pay_method": "cash",
         "subtotal": "100000", "discount": "0", "total": "100000",
         "status": "awaiting_verify", "items": [{"name": "Gul", "qty": 2, "line_total": "100000"}],
         "payment": {"id": 9, "method": "cash", "required_amount": "50000",
                     "received": "0", "remaining": "50000", "status": "awaiting_advance_payment"}}
    o.update(kw)
    return o


class TextsTest(unittest.TestCase):
    def test_status_labels(self):
        self.assertEqual(st_label("awaiting_verify"), "🔎 Chek tekshirilmoqda")
        self.assertEqual(st_label("delivered"), "🏁 Yetkazildi")

    def test_order_text(self):
        t = order_text(mkorder())
        for needle in ["🛍 <b>Buyurtma FAX-000005</b>", "👤 Mijoz", "🧾 Tarkib",
                       "💰 Hisob", "Oldindan", "Qolgan", "<pre>1."]:
            self.assertIn(needle, t)

    def test_keyboards(self):
        kb = order_keyboard(mkorder(status="awaiting_verify"))
        cbs = [b["callback_data"] for row in kb["inline_keyboard"] for b in row]
        self.assertIn("order:5:confirmed", cbs)
        self.assertIn("orders:10", cbs)
        self.assertIsNone(order_keyboard(mkorder(status="closed")))
        self.assertIsNone(order_keyboard(mkorder(status="cancelled")))

    def test_payment_instructions(self):
        t = payment_instructions(mkorder(), {"cardholder": "AZIZ", "card_number": "8600123456789012"})
        self.assertIn("8600 1234 5678 9012", t)
        self.assertIn("MUHIM", t)

    def test_user_status(self):
        self.assertIn("FAX-000005", user_status_text(mkorder()))


class WizardTest(unittest.TestCase):
    def test_add_store_validation(self):
        B.pending[1] = {"step": 0, "data": {}}
        self.assertIsNotNone(B.add_store(1, "name", "ab"))
        self.assertIsNone(B.add_store(1, "name", "Qizil atirgul"))
        self.assertIsNotNone(B.add_store(1, "price", "x"))
        self.assertIsNone(B.add_store(1, "price", "100000"))
        self.assertIsNone(B.add_store(1, "old", "-"))
        self.assertIsNone(B.add_store(1, "stock", "10"))
        self.assertIsNotNone(B.add_store(1, "stock", "-3"))
        self.assertIsNone(B.add_store(1, "desc", "-"))
        B.pending.pop(1, None)

    def test_step_keyboards(self):
        cats = [{"slug": "a", "name_uz": "A"}]
        for step in B.ADD_STEPS:
            kb = B.add_step_kb(step, cats)
            self.assertTrue(kb["inline_keyboard"])
            if step == "cat":
                self.assertIn("padd:cat:a", kb["inline_keyboard"][0][0]["callback_data"])
        self.assertIn("padd:cancel", str(B.add_step_kb("price", [{"slug": "a", "name_uz": "A"}])))


if __name__ == "__main__":
    unittest.main(verbosity=1)
