"""Importa avisos encaminhados por administradores ao bot existente."""
import hashlib
from html import escape
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from offer_storage import command
from coupons import parse_coupon, save_coupon, active_coupons, coupon_block


async def publish_coupon(bot, coupon):
    """Mesmo registro e antirrepetição para encaminhamentos e leitor automático."""
    save_coupon(coupon)
    signature = hashlib.sha256((coupon['code'] + coupon['conditions']).encode()).hexdigest()
    key = 'coupon_notice_' + signature
    if command('GET', key):
        return False
    notice = ('🎟️ <b>Cupom Mercado Livre recebido</b>\n\n'
              + coupon_block({'coupon': coupon})
              + '\n\nCondições do aviso:\n' + escape(coupon['conditions'])
              + '\n\nCódigo recebido pelo bot; validade e aplicação não verificadas no checkout.')
    await bot.send_message(TELEGRAM_CHAT_ID, notice, parse_mode='HTML')
    command('SET', key, '1', 'EX', 7 * 86400)
    return True


async def sync_coupons():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return {'status': 'erro', 'motivo': 'Telegram não configurado'}
    async with Bot(TELEGRAM_BOT_TOKEN) as bot:
        webhook = await bot.get_webhook_info()
        if webhook.url:
            return {'status': 'pendente', 'motivo': 'Bot já usa webhook; integrar recebimento sem removê-lo'}
        offset = int(command('GET', 'coupon_inbox_offset') or 0)
        updates = await bot.get_updates(offset=offset, limit=100, timeout=0)
        accepted, announced, codes, unparsed = 0, 0, [], []
        for update in updates:
            message = update.effective_message
            if message and message.from_user and not message.from_user.is_bot:
                # Apenas o grupo configurado ou um administrador dele no privado.
                allowed = str(message.chat_id) == str(TELEGRAM_CHAT_ID)
                if not allowed and message.chat.type == 'private':
                    try:
                        member = await bot.get_chat_member(TELEGRAM_CHAT_ID, message.from_user.id)
                        allowed = member.status in ('creator', 'administrator')
                    except Exception:
                        allowed = False
                text = message.text or message.caption or ''
                coupon = parse_coupon(text) if allowed else None
                if allowed and not coupon and 'cup' in text.lower():
                    unparsed.append({"motivo": "Código, loja ou validade não reconhecidos", "tem_legenda": bool(message.caption)})
                if coupon:
                    accepted += 1
                    codes.append(coupon['code'])
                    if await publish_coupon(bot, coupon):
                        announced += 1
            command('SET', 'coupon_inbox_offset', str(update.update_id + 1))
        return {'status': 'sucesso', 'updates': len(updates), 'recebidos': accepted,
                'anunciados': announced, 'codigos': codes, 'ativos': len(active_coupons()),
                'avisos_nao_interpretados': unparsed[:3],
                'bot_username': bot.bot.username,
                'le_todas_mensagens_grupo': bool(bot.bot.can_read_all_group_messages)}
