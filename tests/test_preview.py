import unittest
from unittest.mock import patch
from api.index import app


class PreviewTests(unittest.TestCase):
    def test_simulation_never_sends(self):
        with patch('api.index.send_promotion_to_telegram') as send:
            response = app.test_client().post('/api/test_match', json={'text': 'Cupom MELI 10% OFF'})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['labels'])
            self.assertFalse(response.json['sent_to_telegram'])
            self.assertFalse(response.json['affiliate_link_generated'])
            send.assert_not_called()

    def test_page(self):
        response = app.test_client().get('/teste')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'/api/test_match', response.data)

    def test_invalid_input(self):
        client = app.test_client()
        for data in ([], {}, {'text': 123}):
            self.assertEqual(client.post('/api/test_match', json=data).status_code, 400)
        self.assertEqual(client.post('/api/test_match', json={'text': 'x' * 12001}).status_code, 400)
