import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from api.index import app
from telegram_poll import collect


class PollTests(unittest.IsolatedAsyncioTestCase):
    async def test_first_call_initializes_without_old_posts(self):
        client = AsyncMock()
        client.get_entity.return_value = SimpleNamespace(id=123, access_hash=456, broadcast=True)
        client.get_messages.return_value = [SimpleNamespace(id=789)]
        def storage(*args):
            return 1 if args[0] == 'INCR' else None
        with patch('telegram_poll.command', side_effect=storage), patch('telegram_poll.publish_coupon') as publish:
            result = await collect(client, AsyncMock(), ['cupombr'])
            self.assertEqual(result['inicializadas'], 1)
            publish.assert_not_called()

    async def test_failed_publish_does_not_advance_cursor(self):
        client = AsyncMock()
        async def messages(*args, **kwargs):
            yield SimpleNamespace(id=10, raw_text='Mercado Livre cupom: MELITESTE 10% OFF hoje')
        client.iter_messages = messages
        state = {'id': 1, 'access_hash': 2, 'cursor': 9}
        calls = []
        def storage(*args):
            calls.append(args)
            if args[0] == 'INCR': return 1
            if args[0] == 'GET': return json.dumps(state)
        with patch('telegram_poll.command', side_effect=storage), patch('telegram_poll.publish_coupon', new_callable=AsyncMock, side_effect=RuntimeError()):
            result = await collect(client, AsyncMock(), ['cupombr'])
            self.assertEqual(len(result['falhas']), 1)
            self.assertFalse(any(c[:2] == ('SET', 'tg_poll_source_cupombr') for c in calls))

    async def test_success_advances_cursor(self):
        client = AsyncMock()
        async def messages(*args, **kwargs):
            yield SimpleNamespace(id=10, raw_text='Mercado Livre cupom: MELITESTE 10% OFF hoje')
        client.iter_messages = messages
        calls = []
        def storage(*args):
            calls.append(args)
            if args[0] == 'INCR': return 1
            if args[0] == 'GET': return json.dumps({'id': 1, 'access_hash': 2, 'cursor': 9})
        with patch('telegram_poll.command', side_effect=storage), patch('telegram_poll.publish_coupon', new_callable=AsyncMock, return_value=True):
            result = await collect(client, AsyncMock(), ['cupombr'])
            self.assertEqual(result['anunciados'], 1)
            self.assertTrue(any(c[:2] == ('SET', 'tg_poll_source_cupombr') and json.loads(c[2])['cursor'] == 10 for c in calls))

    def test_secret_required_before_storage(self):
        with patch.dict('os.environ', {'TELEGRAM_POLL_SECRET': 'test-secret'}), patch('telegram_poll.command') as storage:
            self.assertEqual(app.test_client().get('/api/telegram/poll').status_code, 401)
            storage.assert_not_called()

    def test_busy_lock(self):
        with patch.dict('os.environ', {'TELEGRAM_POLL_SECRET': 'test-secret'}), patch('telegram_poll.command', return_value=None):
            response = app.test_client().get('/api/telegram/poll', headers={'Authorization': 'Bearer test-secret'})
            self.assertEqual(response.json['status'], 'ignorado')
