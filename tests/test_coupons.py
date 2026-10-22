from datetime import datetime
import unittest
from unittest.mock import patch
from coupons import parse_coupon, compatible, savings, coupon_block, ZONE


class CouponTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2030, 10, 22, 12, tzinfo=ZONE)
        self.coupon = parse_coupon('Mercado Livre — Cupom: MELITESTE 10% OFF em todo site. Compra mínima de R$ 100,00, limitado a R$ 200. Válido até 23/10/2030.', now=self.now)
        self.product = {'source': 'ml', 'name': 'Nintendo Switch 2', 'category': 'Games', 'discount_price': '3500'}

    def test_rules_and_cap(self):
        self.assertEqual(self.coupon['code'], 'MELITESTE')
        self.assertEqual(self.coupon['min_value'], 100)
        self.assertEqual(savings(self.product, self.coupon), 200)
        self.assertTrue(compatible(self.product, self.coupon))

    def test_no_cross_store_or_below_minimum(self):
        self.assertFalse(compatible({**self.product, 'source': 'shopee'}, self.coupon))
        self.assertFalse(compatible({**self.product, 'discount_price': '99'}, self.coupon))

    def test_unknown_expiry_never_attached(self):
        coupon = parse_coupon('Mercado Livre cupom: TESTE10 10% OFF todo site mínimo R$ 100 até R$ 200', now=self.now)
        self.assertFalse(compatible(self.product, coupon))

    def test_restrictions_block_automatic_attachment(self):
        self.assertFalse(compatible(self.product, {**self.coupon, 'restricted': True}))

    def test_category_compatibility(self):
        coupon = {**self.coupon, 'all_site': False, 'terms': ['cadeira']}
        self.assertFalse(compatible(self.product, coupon))
        self.assertTrue(compatible({**self.product, 'name': 'Cadeira ergonômica'}, coupon))

    def test_expired_rejected(self):
        self.assertIsNone(parse_coupon('Mercado Livre cupom: VELHO10 10% OFF válido até 01/01/2020', now=self.now))

    def test_no_code_no_guess(self):
        self.assertIsNone(parse_coupon('Mercado Livre tem cupons de 10% hoje', now=self.now))

    def test_render_preserves_conditions_and_conditional_price(self):
        result = coupon_block({**self.product, 'coupon': self.coupon, 'coupon_savings': 200})
        self.assertIn('MELITESTE', result)
        self.assertIn('limitado a R$ 200', result)
        self.assertIn('se elegível: R$ 3.300,00', result)

    def test_no_percent_without_cap(self):
        self.assertFalse(compatible(self.product, {**self.coupon, 'max_discount': None}))
