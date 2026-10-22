"""Redis REST: falha explícita e exclusão mútua entre disparos do cron."""
from functools import wraps
import uuid
import requests
from ml_oauth import KV_URL, KV_TOKEN


def command(*args):
    if not KV_URL or not KV_TOKEN:
        raise RuntimeError('Configure Redis para persistir o histórico de ofertas.')
    response = requests.post(KV_URL, json=list(args),
                             headers={'Authorization': f'Bearer {KV_TOKEN}'}, timeout=8)
    response.raise_for_status()
    body = response.json()
    if body.get('error'):
        raise RuntimeError('Redis recusou a operação de histórico.')
    return body.get('result')


def get(key):
    return command('GET', key)


def set_value(key, value):
    return command('SET', key, value, 'EX', 8 * 86400) == 'OK'


def serialized_cron(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        token = uuid.uuid4().hex
        try:
            if command('SET', 'offers_cron_lock', token, 'NX', 'EX', 3600) != 'OK':
                return {'status': 'ignorado', 'motivo': 'Disparo já em execução'}, 409
        except Exception:
            return {'status': 'erro', 'motivo': 'Histórico indisponível; nenhum envio realizado'}, 503
        try:
            return function(*args, **kwargs)
        finally:
            try:
                command('EVAL', "if redis.call('get',KEYS[1]) == ARGV[1] then return redis.call('del',KEYS[1]) else return 0 end", 1, 'offers_cron_lock', token)
            except Exception:
                pass  # A trava expira; nunca remove a trava de outro processo.
    return wrapped
