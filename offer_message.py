"""Mensagem determinística, sem urgência, cupom ou desconto inventados."""
from html import escape


def money(value):
    return f'{float(value):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def generate_ad_text(product_name, original_price, discount_price, category):
    title = escape(str(product_name)[:300])
    current = float(discount_price or 0)
    original = float(original_price or 0)
    lines = [f'<b>{title}</b>', escape(str(category)[:80])]
    if original > current > 0:
        lines.append(f'De R$ {money(original)}')
    if current > 0:
        lines.append(f'<b>R$ {money(current)}</b>')
    lines.append('Preço informado pela loja; confira frete e condições no link.')
    return '\n\n'.join(lines)
