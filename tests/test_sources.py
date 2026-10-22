import unittest
from unittest.mock import AsyncMock, patch
from telethon.tl.types import PeerChannel
from telegram_watch import resolve_sources, import_source_coupon


class SourcesTests(unittest.IsolatedAsyncioTestCase):
    async def test_username_allowlist_resolves_real_ids(self):
        client = AsyncMock()
        client.get_entity.side_effect = [PeerChannel(111), PeerChannel(222)]
        ids = await resolve_sources(client, {'chat_usernames': ['cupombr', '@cupomvalido'], 'watch_all_groups': False})
        self.assertEqual(ids, {-1000000000111, -1000000000222})
        self.assertEqual(client.get_entity.await_count, 2)

    async def test_inaccessible_source_fails_startup(self):
        client = AsyncMock()
        client.get_entity.side_effect = ValueError('not found')
        with self.assertRaisesRegex(RuntimeError, 'cupombr'):
            await resolve_sources(client, {'chat_usernames': ['cupombr']})

    async def test_empty_selection_does_not_read_every_group(self):
        with self.assertRaises(ValueError):
            await resolve_sources(AsyncMock(), {'watch_all_groups': False})

    async def test_coupon_uses_shared_registry_and_group_publisher(self):
        text = 'Mercado Livre cupom: MELITESTE 10% OFF hoje, todo site, mínimo R$ 100, limitado a R$ 200'
        bot = AsyncMock()
        with patch('telegram_watch.publish_coupon', new_callable=AsyncMock) as publish:
            result = await import_source_coupon(text, {'publish_coupons_to_group': True}, bot)
            self.assertTrue(result)
            self.assertEqual(publish.await_args.args[1]['code'], 'MELITESTE')

    async def test_shopee_not_imported_as_ml_coupon(self):
        with patch('telegram_watch.publish_coupon', new_callable=AsyncMock) as publish:
            result = await import_source_coupon('Shopee cupom: SHOPEE10 10% OFF hoje', {'publish_coupons_to_group': True}, AsyncMock())
            self.assertFalse(result)
            publish.assert_not_awaited()
