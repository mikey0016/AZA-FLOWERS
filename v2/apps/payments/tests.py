"""To'lov matematikasi testlari: 50% naqd, 100% karta, yaxlitlash."""
from decimal import Decimal
from django.test import TestCase

from apps.payments.models import money, split_payment


class MoneyTest(TestCase):
    def test_cash_50(self):
        adv, rest = split_payment(Decimal("200000"), "cash", 50)
        self.assertEqual(adv, Decimal("100000"))
        self.assertEqual(rest, Decimal("100000"))

    def test_card_100(self):
        adv, rest = split_payment(Decimal("200000"), "card")
        self.assertEqual(adv, Decimal("200000"))
        self.assertEqual(rest, Decimal("0"))

    def test_rounding_sum(self):
        # advance + remaining har doim total ga teng (toq summalar)
        for total in ["1", "99", "199999", "333333", "1000000"]:
            adv, rest = split_payment(Decimal(total), "cash", 50)
            self.assertEqual(adv + rest, Decimal(total), total)

    def test_money_quantize(self):
        self.assertEqual(money(100), Decimal("100"))
        self.assertEqual(money("10.5"), Decimal("11"))  # ROUND_HALF_UP
