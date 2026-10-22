"""Coleta curta por chamada HTTP; sessão e cursores persistem fora do processo."""
import asyncio
import hmac
import json
import os
from pathlib import Path
import time
import uuid

from flask import Blueprint, jsonify, request
from offer_storage import command
from coupons import parse_coupon
from coupon_inbox import publish_coupon

poll_api = Blueprint('telegram_poll', __name__)
CONFIG = json.loads(Path(__file__).with_name('watchlist.json').read_text(encoding='utf-8'))


async def collect(client, bot, sources, budget=20):
    """Primeira execução posiciona no presente; seguintes consomem até 20 posts/fonte."""
    from telethon.tl.types import InputPeerChannel
    started = time.monotonic()
    result = {'fontes': 0, 'mensagens': 0, 'cupons': 0, 'anunciados': 0, 'inicializadas': 0, 'falhas': []}
    # Alterna a primeira fonte para não deixar a última sem tempo em todas as chamadas.
    rotation = int(command('INCR', 'tg_poll_rotation')) % len(sources)
    ordered = sources[rotation:] + sources[:rotation]
    for name in ordered:
        if time.monotonic() - started >= budget:
            break
        key = 'tg_poll_source_' + name.lower()
        try:
            raw = command('GET', key)
            state = json.loads(raw) if raw else None
            if not state:
                entity = await client.get_entity(name)
                if not getattr(entity, 'broadcast', False) and not getattr(entity, 'megagroup', False):
                    raise ValueError('Fonte não é grupo/canal')
                latest = await client.get_messages(entity, limit=1)
                state = {'id': entity.id, 'access_hash': entity.access_hash,
                         'cursor': latest[0].id if latest else 0}
                command('SET', key, json.dumps(state))
                result['inicializadas'] += 1
                result['fontes'] += 1
                continue
            peer = InputPeerChannel(state['id'], state['access_hash'])
            async for message in client.iter_messages(peer, min_id=state['cursor'], reverse=True, limit=20):
                if time.monotonic() - started >= budget:
                    break
                text = message.raw_text or ''
                coupon = parse_coupon(text)
                if coupon:
                    # Posts com múltiplos códigos exigem revisão de escopo por cupom.
                    result['cupons'] += 1
                    if await publish_coupon(bot, coupon):
                        result['anunciados'] += 1
                # Só avança depois de salvar/anunciar; falha preserva a mensagem para retry.
                state['cursor'] = message.id
                command('SET', key, json.dumps(state))
                result['mensagens'] += 1
            result['fontes'] += 1
        except Exception as exc:
            result['falhas'].append({'fonte': name, 'erro': type(exc).__name__})
    command('SET', 'tg_poll_last_result', json.dumps({**result, 'at': int(time.time())}))
    return result


async def run_poll():
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telegram import Bot
    from config import TELEGRAM_BOT_TOKEN
    required = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_USER_SESSION']
    if not all(os.getenv(key) for key in required) or not TELEGRAM_BOT_TOKEN:
        return {'status': 'pendente', 'motivo': 'Login da conta ainda não configurado no ambiente online'}, 503
    client = TelegramClient(StringSession(os.environ['TELEGRAM_USER_SESSION']),
                            int(os.environ['TELEGRAM_API_ID']), os.environ['TELEGRAM_API_HASH'],
                            connection_retries=1, request_retries=1, flood_sleep_threshold=0,
                            receive_updates=False, timeout=5)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return {'status': 'pendente', 'motivo': 'Sessão revogada; refaça o login local'}, 503
        async with Bot(TELEGRAM_BOT_TOKEN) as bot:
            result = await collect(client, bot, CONFIG['chat_usernames'])
        return {'status': 'sucesso', **result}, 200
    finally:
        await client.disconnect()


@poll_api.route('/api/telegram/poll', methods=['GET', 'POST'])
def poll():
    secret = os.getenv('TELEGRAM_POLL_SECRET', '')
    if not secret or not hmac.compare_digest(request.headers.get('Authorization', ''), 'Bearer ' + secret):
        return jsonify(status='erro', motivo='Não autorizado'), 401
    token = uuid.uuid4().hex
    try:
        if command('SET', 'tg_poll_lock', token, 'NX', 'EX', 120) != 'OK':
            return jsonify(status='ignorado', motivo='Coleta já em execução'), 200
    except Exception:
        return jsonify(status='erro', motivo='Armazenamento indisponível'), 503
    try:
        result, status = asyncio.run(asyncio.wait_for(run_poll(), timeout=25))
        return jsonify(result), status
    except asyncio.TimeoutError:
        return jsonify(status='parcial', motivo='Tempo da chamada esgotado; cursores preservados'), 200
    except Exception as exc:
        return jsonify(status='erro', motivo=type(exc).__name__), 503
    finally:
        try:
            command('EVAL', "if redis.call('get',KEYS[1]) == ARGV[1] then return redis.call('del',KEYS[1]) else return 0 end", 1, 'tg_poll_lock', token)
        except Exception:
            pass
