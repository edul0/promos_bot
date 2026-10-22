"""Histórico persistente: mesma oferta só volta após 7 dias ou queda de 3%."""
import hashlib
import json
import re
import time
import unicodedata

from offer_storage import get as kv_get, set_value as kv_set


def normalize(text):
    text = unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode().lower()
    return ' '.join(re.findall(r'[a-z0-9]+', text))


def offer_key(product):
    # Título evita repetir o mesmo modelo com outro link de afiliado.
    identity = normalize(product.get('source', 'ml')) + ':' + normalize(product['name'])
    return 'offer_v2_' + hashlib.sha256(identity.encode()).hexdigest()


def eligible(product, now=None):
    try:
        price = float(product.get('discount_price') or 0)
        if price <= 0 or not product.get('affiliate_link'):
            return False
        raw = kv_get(offer_key(product))
        if not raw:
            return True
        last = json.loads(raw)
        now = time.time() if now is None else now
        return now - last['sent_at'] >= 7 * 86400 or price <= last['price'] * .97
    except (ValueError, TypeError, KeyError):
        return False


def record_sent(product, now=None):
    return kv_set(offer_key(product), json.dumps({
        'price': float(product['discount_price']),
        'sent_at': time.time() if now is None else now,
    }))
