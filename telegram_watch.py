"""Leitor das fontes escolhidas: cupons no grupo e ofertas de interesse no privado."""
import argparse
import asyncio
import hashlib
from html import escape
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
import time
import unicodedata

from dotenv import load_dotenv

load_dotenv()
from affiliate_urls import own_ml_link
from coupons import parse_coupon
from coupon_inbox import publish_coupon
log = logging.getLogger(__name__)


def normalize(text):
    return ' '.join(unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower().split())


def announced_price(text):
    # Sem inferir preço final de cupom, parcelas, frete ou desconto percentual.
    found = re.search(r'R\$\s*(\d[\d.]*)(?:,(\d{2}))?', text, re.I)
    if not found:
        return None
    return float(found[1].replace('.', '') + '.' + (found[2] or '00'))


def match_labels(text, config):
    plain = normalize(text)
    labels = []
    if config.get('coupon_alerts') and re.search(r'\b(cupom|cupons|coupon)\b', plain):
        labels.append('Cupom mencionado — conferir validade e elegibilidade')
    # URLs precisam pertencer ao domínio, não apenas conter o nome da loja.
    ml = bool(re.search(r'https?://(?:[\w-]+\.)*(?:mercadolivre\.com(?:\.br)?|meli\.la)(?=[/:?#\s]|$)', text, re.I))
    for interest in config.get('interests', []):
        if not any(normalize(term) in plain for term in interest['terms']):
            continue
        if any(normalize(term) in plain for term in interest.get('exclude', [])):
            continue
        if interest.get('store') == 'ml' and not ml:
            continue
        limit = interest.get('max_price')
        price = announced_price(text)
        if limit is not None and (price is None or price > float(limit)):
            continue
        labels.append(interest['name'])
    return labels


def fingerprint(text):
    # Ignora diferentes links de afiliado para posts com o mesmo texto/preço.
    plain = normalize(re.sub(r'https?://\S+', '', text))
    return hashlib.sha256(plain.encode()).hexdigest()


async def resolve_sources(client, config):
    from telethon.utils import get_peer_id
    selected = set(int(i) for i in config.get('chat_ids', []))
    for username in config.get('chat_usernames', []):
        try:
            entity = await client.get_entity(username.lstrip('@'))
            selected.add(get_peer_id(entity))
        except Exception as exc:
            raise RuntimeError(f'Não foi possível acessar @{username}: {type(exc).__name__}') from None
    if not config.get('watch_all_groups') and not selected:
        raise ValueError('Escolha chat_ids ou chat_usernames.')
    return selected


async def import_source_coupon(text, config, bot):
    if not config.get('publish_coupons_to_group'):
        return False
    coupon = parse_coupon(text)
    if not coupon:
        return False
    await publish_coupon(bot, coupon)
    return True


async def run(args):
    from telethon import TelegramClient, events
    from telegram import Bot
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    data = Path(os.getenv('WATCH_DATA_DIR', 'data'))
    data.mkdir(parents=True, exist_ok=True)
    api_id = int(os.environ['TELEGRAM_API_ID'])
    api_hash = os.environ['TELEGRAM_API_HASH']
    client = TelegramClient(str(data / 'telegram_user'), api_id, api_hash,
                            sequential_updates=True, auto_reconnect=True)
    if args.login or args.list_chats:
        await client.start()
        if args.list_chats:
            async for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    print(f'{dialog.id}\t{dialog.name}')
        await client.disconnect()
        return
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        raise RuntimeError('Execute primeiro: python telegram_watch.py --login')
    destination = int(os.getenv('TELEGRAM_ALERT_CHAT_ID') or 0)
    if destination < 0:
        raise ValueError('TELEGRAM_ALERT_CHAT_ID deve ser seu chat privado, com ID positivo.')
    bot = Bot(os.environ['TELEGRAM_BOT_TOKEN'])
    db = sqlite3.connect(data / 'alerts.sqlite3')
    db.execute('CREATE TABLE IF NOT EXISTS sent (fingerprint TEXT PRIMARY KEY, sent_at REAL NOT NULL)')
    selected = await resolve_sources(client, config)
    if config.get('publish_coupons_to_group'):
        from config import TELEGRAM_CHAT_ID
        if not TELEGRAM_CHAT_ID:
            raise ValueError('Configure TELEGRAM_CHAT_ID para os avisos de cupom.')
        if int(TELEGRAM_CHAT_ID) in selected:
            raise ValueError('O grupo de destino não pode ser uma fonte de cupons.')

    async def handle(event):
        if event.out or not (event.is_group or event.is_channel):
            return
        if not config.get('watch_all_groups') and event.chat_id not in selected:
            return
        text = event.raw_text or ''
        # Não usa links comerciais do rival: publica apenas código e condições.
        if await import_source_coupon(text, config, bot):
            return
        if not destination:
            return
        labels = match_labels(text, config)
        if not labels:
            return
        key = fingerprint(text)
        now = time.time()
        previous = db.execute('SELECT sent_at FROM sent WHERE fingerprint=?', (key,)).fetchone()
        if previous and now - previous[0] < 7 * 86400:
            return
        links = re.findall(r'https?://[^\s<>]+', text)
        own_links = []
        for url in dict.fromkeys(links):
            own = await asyncio.to_thread(own_ml_link, url.rstrip(').,'))
            if own and own not in own_links:
                own_links.append(own)
        is_coupon = any(label.startswith('Cupom mencionado') for label in labels)
        if not own_links and not is_coupon:
            log.info('Oferta retida: não foi possível gerar link próprio.')
            return
        clean_text = re.sub(r'https?://[^\s<>]+', '[link da origem removido]', text)
        chat = await event.get_chat()
        username = getattr(chat, 'username', None)
        source = f'https://t.me/{username}/{event.id}' if username else None
        if not source and str(event.chat_id).startswith('-100'):
            source = f'https://t.me/c/{str(event.chat_id)[4:]}/{event.id}'
        lines = [f'<b>{escape(label)}</b>' for label in labels]
        lines += [f'Origem: {escape(getattr(chat, "title", "Grupo"))}',
                  'Condições e preço anunciados na mensagem; não verificados no checkout.',
                  escape(clean_text[:2200])]
        if own_links:
            lines.append('Comprar com seu link de afiliado:\n' + '\n'.join(escape(url) for url in own_links[:3]))
        else:
            lines.append('Aviso de cupom, sem link de compra convertido.')
        if source:
            lines.append(f'<a href="{source}">Abrir mensagem original</a>')
        try:
            await bot.send_message(destination, '\n\n'.join(lines), parse_mode='HTML')
        except Exception as exc:
            log.error('Alerta não enviado (%s); sem gravar como entregue.', type(exc).__name__)
            return
        db.execute('INSERT OR REPLACE INTO sent VALUES (?, ?)', (key, now))
        db.execute('DELETE FROM sent WHERE sent_at < ?', (now - 8 * 86400,))
        db.commit()

    async def safe_handle(event):
        try:
            await handle(event)
        except Exception as exc:
            log.error('Falha ao processar mensagem (%s).', type(exc).__name__)

    client.add_event_handler(safe_handle, events.NewMessage())
    client.add_event_handler(safe_handle, events.MessageEdited())
    try:
        async with bot:
            log.info('Leitor ativo: %s fontes; cupons no grupo configurado.', len(selected))
            await client.run_until_disconnected()
    finally:
        db.close()
        await client.disconnect()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--login', action='store_true')
    parser.add_argument('--list-chats', action='store_true')
    parser.add_argument('--config', default='watchlist.json')
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run(parser.parse_args()))
