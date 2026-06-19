import google.generativeai as genai
from config import GEMINI_API_KEY
import random

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def _price_block(original_price, discount_price):
    """Monta o bloco de preço só quando há valores reais (sem inventar)."""
    has_disc = bool(discount_price) and discount_price not in ("0.00", "0")
    has_orig = bool(original_price) and original_price not in ("0.00", "0")
    if has_disc and has_orig and original_price != discount_price:
        return f"❌ De: R$ {original_price}\n✅ Por apenas: R$ {discount_price}"
    if has_disc:
        return f"💰 Por apenas: R$ {discount_price}"
    return ""  # sem preço real


def generate_ad_text(product_name, original_price, discount_price, category):
    """
    Cria uma copy persuasiva para o Telegram. Mostra preço só quando é real;
    se não houver preço, foca no produto ser destaque/mais vendido.
    """
    price_block = _price_block(original_price, discount_price)

    if not GEMINI_API_KEY:
        if price_block:
            return f"🔥 OFERTA IMPERDÍVEL: {product_name}!\n\n{price_block}\n\n🎟️ Confira cupons no APP para descontos extras!\n\nCorre que é um dos mais vendidos! 👇"
        return f"🔥 DESTAQUE: {product_name}!\n\n🏆 Um dos MAIS VENDIDOS em {category}!\n\n🎟️ Veja o preço e cupons no link 👇"

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        if price_block:
            preco_info = f"Preço original: R$ {original_price}\nPreço atual: R$ {discount_price}"
            regra_preco = "Destaque o preço/desconto de forma chamativa."
        else:
            preco_info = "Preço: não informado (NÃO invente preços!)"
            regra_preco = "NÃO invente preços. Destaque que é um dos MAIS VENDIDOS da categoria e chame pra ver a oferta no link."

        prompt = f"""
        Você é um copywriter especialista em vendas e promoções para Telegram.
        Crie um anúncio curto (máximo 4 linhas), muito persuasivo, cheio de emojis.

        Produto: {product_name}
        Categoria: {category}
        {preco_info}

        Regras:
        1. Comece com um gatilho de urgência (Ex: ALERTA DE OFERTA, CORRE, TOP VENDAS).
        2. {regra_preco}
        3. Sugira verificar cupons no APP do Mercado Livre.
        4. Texto curto para leitura rápida no celular.
        """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Erro na IA: {e}")
        if price_block:
            return f"🔥 OFERTA SURREAL: {product_name}!\n\n{price_block}\n\n🎟️ Aplique cupons no carrinho!\n\nAproveite antes que esgote! 👇"
        return f"🔥 TOP VENDAS: {product_name}!\n\n🏆 Um dos mais procurados em {category}!\n\n🎟️ Veja o preço e cupons no link 👇"
