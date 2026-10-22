import json
from pathlib import Path
import unittest
from unittest.mock import patch, Mock

import offer_history as history
from offer_message import generate_ad_text
from telegram_watch import match_labels, fingerprint
from affiliate_urls import own_ml_link
from shopee_api import _match_category


class OffersTests(unittest.TestCase):
    def setUp(self):
        self.product = {'source': 'ml', 'name': 'Nintendo Switch 2',
                        'discount_price': '3000', 'affiliate_link': 'https://meli.la/own'}
        self.config = json.loads((Path(__file__).resolve().parents[1] / 'watchlist.json').read_text())

    def test_same_offer_blocked_after_restart(self):
        with patch.object(history, 'kv_get', return_value=json.dumps({'price': 3000, 'sent_at': 1000})):
            self.assertFalse(history.eligible(self.product, now=2000))

    def test_real_price_drop_allowed(self):
        with patch.object(history, 'kv_get', return_value=json.dumps({'price': 3200, 'sent_at': 1000})):
            self.assertTrue(history.eligible(self.product, now=2000))

    def test_expired_history_allows_offer(self):
        with patch.object(history, 'kv_get', return_value=json.dumps({'price': 3000, 'sent_at': 1000})):
            self.assertTrue(history.eligible(self.product, now=1000 + 8 * 86400))

    def test_missing_price_or_link_blocked(self):
        self.assertFalse(history.eligible({**self.product, 'discount_price': ''}))
        self.assertFalse(history.eligible({**self.product, 'affiliate_link': None}))

    def test_other_affiliate_url_does_not_bypass_history(self):
        self.assertEqual(history.offer_key(self.product), history.offer_key({**self.product, 'affiliate_link': 'other'}))

    def test_switch_only_ml(self):
        self.assertTrue(match_labels('Nintendo Switch 2 https://mercadolivre.com.br/p/MLB123', self.config))
        self.assertFalse(match_labels('Nintendo Switch 2 https://shopee.com.br/123', self.config))
        self.assertFalse(match_labels('Nintendo Switch 2 https://mercadolivre.com.br.fake.test/123', self.config))

    def test_switch_accessory_ignored(self):
        self.assertFalse(match_labels('Capa Switch 2 https://meli.la/test', self.config))

    def test_ergonomic_chair(self):
        self.assertTrue(match_labels('Cadeira ergonômica R$ 890', self.config))
        self.assertFalse(match_labels('Cadeira gamer infantil', self.config))

    def test_coupons_without_product_or_price(self):
        self.assertTrue(match_labels('CUPOM: MELITECH 10% OFF, máximo R$ 200, apenas app', self.config))

    def test_dedup_across_affiliate_links(self):
        self.assertEqual(fingerprint('Cupom ABC https://meli.la/a'), fingerprint('Cupom ABC https://meli.la/b'))
        self.assertNotEqual(fingerprint('Cupom ABC 10%'), fingerprint('Cupom ABC 20%'))

    def test_price_limit(self):
        self.config['interests'][0]['max_price'] = 3500
        self.assertFalse(match_labels('Switch 2 R$ 3.800,00 https://meli.la/a', self.config))
        self.assertTrue(match_labels('Switch 2 R$ 3.400,00 https://meli.la/a', self.config))

    def test_reject_rival_and_unsafe_hosts(self):
        with patch('affiliate_urls.requests.get') as get:
            self.assertIsNone(own_ml_link('https://shopee.com.br/a'))
            self.assertIsNone(own_ml_link('https://mercadolivre.com.br.fake.test/MLB123'))
            get.assert_not_called()

    def test_only_official_generator_and_strip_rival_query(self):
        with patch('affiliate_urls.generate_official_affiliate_link', return_value='https://meli.la/own') as generate:
            self.assertEqual(own_ml_link('https://www.mercadolivre.com.br/p/MLB123?matt_word=rival'), 'https://meli.la/own')
            generate.assert_called_once_with('https://www.mercadolivre.com.br/p/MLB123')

    def test_failed_generator_no_fallback(self):
        with patch('affiliate_urls.generate_official_affiliate_link', return_value=None):
            self.assertIsNone(own_ml_link('https://www.mercadolivre.com.br/p/MLB123'))

    def test_variety_includes_other_categories(self):
        self.assertEqual(_match_category({'name': 'Panela inox', 'category_raw': 'Cozinha'}), 'Cozinha')

    def test_html_escape_and_no_fake_discount(self):
        text = generate_ad_text('<cadeira>', '', '899', 'Escritório')
        self.assertIn('&lt;cadeira&gt;', text)
        self.assertNotIn('De R$', text)
        self.assertNotIn('cupom', text.lower())


if __name__ == '__main__':
    unittest.main()
