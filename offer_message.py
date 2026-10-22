"""Mensagem determinística, sem urgência, cupom ou desconto inventados."""
from html import escape


def money(value):
    return f'{float(value):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def generate_ad_text(product_name, original_price, discount_price, category):
    title = escape(str(product_name)[:300])
    current = float(discount_price or 0)
    original = float(original_price or 0)
    lines = [f'🛍 <b>VISTALL PROMOS</b>\n<i>{escape(str(category)[:80])}</i>', f'<b>{title}</b>']
    if original > current > 0:
        lines.append(f'De <s>R$ {money(original)}</s>\n💰 <b>R$ {money(current)}</b>')
    elif current > 0:
        lines.append(f'💰 <b>R$ {money(current)}</b>')
    return '\n\n'.join(lines)
