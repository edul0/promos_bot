"""Cupons recebidos no Telegram; cálculo sempre condicionado à elegibilidade."""
from datetime import datetime, timedelta
from decimal import Decimal
from html import escape
import json
import re
from zoneinfo import ZoneInfo

from offer_history import normalize
from offer_storage import command

ZONE = ZoneInfo('America/Sao_Paulo')


def amount(value):
    return float(value.replace('.', '').replace(',', '.'))


def parse_coupon(text, now=None):
    now = now or datetime.now(ZONE)
    plain = normalize(text)
    if not re.search(r'\b(cupom|cupons)\b', plain):
        return None
    if not any(term in plain for term in ('mercado livre', 'mercadolivre', 'meli')):
        return None
    # Só aceita código explicitamente identificado; não infere código de links.
    codes = re.findall(r'(?:cupom|c[oó]digo)\s*(?:de desconto\s*)?[:=\-]?\s*[`*\s]*([A-Z0-9]{4,35})\b', text, re.I)
    codes = [code.upper() for code in codes if code.upper() not in {'MERCADO', 'LIVRE', 'DESCONTO', 'CUPOM', 'CUPONS'} and not code.isdigit()]
    if not codes:
        return None
    code = codes[0]
    if code in {'MERCADO', 'LIVRE', 'DESCONTO', 'CUPOM', 'CUPONS'} or code.isdigit():
        return None
    percent = re.search(r'(\d{1,2}(?:[,.]\d+)?)\s*%\s*(?:OFF|de desconto)', text, re.I)
    fixed = re.search(r'R\$\s*([\d.]+(?:,\d{2})?)\s*(?:OFF|de desconto)', text, re.I)
    minimum = re.search(r'(?:acima de|a partir de|m[ií]nim[oa](?: de)?|m[ií]n\.?)\s*R\$\s*([\d.]+(?:,\d{2})?)', text, re.I)
    cap = re.search(r'(?:limitad[oa](?: a)?|m[aá]ximo(?: de)?|at[eé])\s*R\$\s*([\d.]+(?:,\d{2})?)', text, re.I)
    expires = None
    date = re.search(r'(?:v[aá]lid[oa] at[eé]|validade:?|expira(?: em)?)\s*(\d{2}/\d{2}/\d{4})', text, re.I)
    try:
        if date:
            expires = datetime.strptime(date[1], '%d/%m/%Y').replace(tzinfo=ZONE) + timedelta(days=1)
        elif re.search(r'\bhoje\b', plain):
            expires = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    except ValueError:
        return None
    # Sem validade clara: aviso por 24h, sem anexar automaticamente a produtos.
    expires_at = (expires or now + timedelta(hours=24)).timestamp()
    if expires_at <= now.timestamp():
        return None
    terms = []
    for label, words in {
        'games': ['games', 'videogame', 'consoles', 'switch'],
        'cadeira': ['cadeiras', 'cadeira', 'moveis', 'escritorio'],
        'informatica': ['informatica', 'computadores', 'notebooks'],
        'celular': ['celulares', 'smartphones'],
    }.items():
        if any(re.search(r'\b' + word + r'\b', plain) for word in words):
            terms.append(label)
    restricted = any(word in plain for word in (
        'primeira compra', 'novos usuarios', 'saldo', 'cartao', 'full', 'resgatou ontem',
        'lojas oficiais', 'produtos selecionados', 'produtos participantes', 'somente para',
    ))
    return {'code': code, 'discount_pct': float(percent[1].replace(',', '.')) if percent else 0,
            'discount_val': amount(fixed[1]) if fixed and not percent else 0,
            'min_value': amount(minimum[1]) if minimum else None,
            'max_discount': amount(cap[1]) if cap else None,
            'expires_at': expires_at, 'expiry_explicit': expires is not None,
            'all_site': 'todo site' in plain or 'site todo' in plain,
            'terms': terms, 'restricted': restricted,
            'platform': 'App do Mercado Livre' if 'app' in plain else 'Mercado Livre',
            'conditions': re.sub(r'https?://\S+', '[link da origem omitido]', text)[:1800]}


def save_coupon(coupon):
    # Mesmo código e condições não disparam outro anúncio. HSET é atômico.
    existing = command('HGET', 'ml_coupons_v1', coupon['code'])
    record = json.dumps(coupon, ensure_ascii=False, sort_keys=True)
    if existing:
        old = json.loads(existing)
        # Janela de retenção de validade desconhecida não torna o cupom "novo".
        comparable = {key: value for key, value in old.items() if key != 'expires_at'}
        current = {key: value for key, value in coupon.items() if key != 'expires_at'}
        if comparable == current and (not coupon['expiry_explicit'] or old['expires_at'] == coupon['expires_at']):
            return False
    command('HSET', 'ml_coupons_v1', coupon['code'], record)
    return True


def active_coupons(now=None):
    now = now or datetime.now(ZONE).timestamp()
    result = command('HGETALL', 'ml_coupons_v1') or []
    pairs = result.items() if isinstance(result, dict) else zip(result[::2], result[1::2])
    active = []
    for code, raw in pairs:
        coupon = json.loads(raw)
        if coupon['expires_at'] <= now:
            command('HDEL', 'ml_coupons_v1', code)
        else:
            active.append(coupon)
    return active


def compatible(product, coupon):
    if product.get('source', 'ml') != 'ml' or not coupon.get('expiry_explicit') or coupon.get('restricted'):
        return False
    if coupon['expires_at'] <= datetime.now(ZONE).timestamp():
        return False
    price = float(product.get('discount_price') or 0)
    if price <= 0 or coupon.get('min_value') is None or price < coupon['min_value']:
        return False
    name = normalize(product['name'] + ' ' + product.get('category', ''))
    aliases = {'games': ('games', 'videogame', 'console', 'switch', 'playstation', 'xbox'),
               'cadeira': ('cadeira',), 'informatica': ('informatica', 'notebook', 'computador'),
               'celular': ('celular', 'smartphone', 'iphone', 'galaxy')}
    if not coupon.get('all_site') and not any(word in name for term in coupon.get('terms', []) for word in aliases[term]):
        return False
    if coupon.get('discount_pct') and coupon.get('max_discount') is None:
        return False
    return bool(coupon.get('discount_pct') or coupon.get('discount_val'))


def savings(product, coupon):
    price = Decimal(str(product['discount_price']))
    reduction = price * Decimal(str(coupon.get('discount_pct') or 0)) / 100
    if not reduction:
        reduction = Decimal(str(coupon.get('discount_val') or 0))
    if coupon.get('max_discount') is not None:
        reduction = min(reduction, Decimal(str(coupon['max_discount'])))
    return float(min(price, reduction).quantize(Decimal('.01')))


def attach_coupon(product):
    if product.get('source', 'ml') != 'ml':
        return product
    candidates = [coupon for coupon in active_coupons() if compatible(product, coupon)]
    if not candidates:
        return product
    best = max(candidates, key=lambda coupon: savings(product, coupon))
    return {**product, 'coupon': best, 'coupon_savings': savings(product, best)}


def coupon_block(product):
    coupon = product.get('coupon') or {}
    if not coupon.get('code'):
        return ''
    lines = [f'🏷️ Cupom: <code>{escape(str(coupon["code"]))}</code>']
    if coupon.get('discount_pct'):
        lines.append(f'{float(coupon["discount_pct"]):g}% OFF')
    elif coupon.get('discount_val'):
        lines.append(f'R$ {float(coupon["discount_val"]):.2f} OFF')
    if coupon.get('min_value') is not None:
        lines.append(f'Compra mínima: R$ {float(coupon["min_value"]):.2f}')
    if coupon.get('max_discount') is not None:
        lines.append(f'Desconto limitado a R$ {float(coupon["max_discount"]):.2f}')
    if coupon.get('expires_at') and coupon.get('expiry_explicit'):
        lines.append('Validade anunciada até ' + datetime.fromtimestamp(coupon['expires_at'] - 1, ZONE).strftime('%d/%m %H:%M'))
    lines.append('Onde usar: ' + escape(str(coupon.get('platform', 'Mercado Livre'))))
    if product.get('coupon_savings'):
        price = float(product['discount_price']) - product['coupon_savings']
        lines.append(f'Com cupom, se elegível: R$ {price:.2f} (estimativa, sem frete).')
    lines.append('Confirme aplicação e regras no carrinho; não cumulativo.')
    return '\n'.join(lines)
