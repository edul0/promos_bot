import unittest
from unittest.mock import patch, AsyncMock
from api import index
from shopee_api import _detect_columns


class DeliveryTests(unittest.TestCase):
    def test_plain_product_url_is_not_an_affiliate_link(self):
        columns = _detect_columns(['title', 'sale_price', 'product_link'])
        self.assertIsNone(columns['url'])

    def test_feed_first_column_is_not_lost(self):
        columns = _detect_columns(['title', 'sale_price', 'price', 'affiliate_link'])
        self.assertEqual(columns['name'], 0)
        self.assertEqual(columns['price'], 1)

    def test_store_unavailable_prevents_send(self):
        with patch('offer_storage.command', side_effect=RuntimeError('offline')), \
                patch.object(index, 'send_promotion_to_telegram', new_callable=AsyncMock) as send:
            response = index.app.test_client().get('/api/cron')
            self.assertEqual(response.status_code, 503)
            send.assert_not_called()

    def test_failed_delivery_not_saved(self):
        with patch('offer_storage.command', return_value='OK'), \
                patch.object(index, 'TELEGRAM_BOT_TOKEN', 'test'), \
                patch.object(index, 'TELEGRAM_CHAT_ID', '123'), \
                patch.object(index, 'kv_get', return_value='shopee'), \
                patch.object(index, 'get_ml_promotions', return_value=[{'name': 'test'}]), \
                patch.object(index, 'send_promotion_to_telegram', new_callable=AsyncMock, return_value=False), \
                patch.object(index, 'attach_coupon', side_effect=lambda p: p), \
                patch.object(index, 'record_sent') as record:
            response = index.app.test_client().get('/api/cron')
            self.assertEqual(response.status_code, 502)
            record.assert_not_called()

    def test_successful_delivery_saved(self):
        product = {'name': 'test', 'category': 'Games', 'affiliate_link': 'https://meli.la/own'}
        with patch('offer_storage.command', return_value='OK'), \
                patch.object(index, 'TELEGRAM_BOT_TOKEN', 'test'), \
                patch.object(index, 'TELEGRAM_CHAT_ID', '123'), \
                patch.object(index, 'kv_get', return_value='shopee'), \
                patch.object(index, 'kv_set', return_value=True), \
                patch.object(index, 'get_ml_promotions', return_value=[product]), \
                patch.object(index, 'send_promotion_to_telegram', new_callable=AsyncMock, return_value=True), \
                patch.object(index, 'attach_coupon', side_effect=lambda p: p), \
                patch.object(index, 'record_sent', return_value=True) as record:
            response = index.app.test_client().get('/api/cron')
            self.assertEqual(response.status_code, 200)
            record.assert_called_once_with(product)
