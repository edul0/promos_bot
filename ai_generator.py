import google.generativeai as genai
from config import GEMINI_API_KEY
import random

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_ad_text(product_name, original_price, discount_price, category):
    """
    Usa a API do Google Gemini para criar uma copy persuasiva de vendas.
    """
    if not GEMINI_API_KEY:
        return f"🔥 PROMOÇÃO IMPERDÍVEL: {product_name}!\n\nDe: R$ {original_price}\nPor apenas: R$ {discount_price}\n\n🎟️ Use o cupom do APP para mais descontos!\n\nCorre que acaba rápido! 👇"

    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""
        Você é um copywriter especialista em vendas e promoções para Telegram.
        Crie um anúncio curto (máximo 4 linhas), muito persuasivo, cheio de emojis.
        
        Produto: {product_name}
        Categoria: {category}
        Preço original: R$ {original_price}
        Preço com desconto: R$ {discount_price}
        
        Regras:
        1. Comece com um gatilho de urgência (Ex: ALERTA DE OFERTA, CORRE, BUG).
        2. Destaque o desconto de forma chamativa.
        3. Fale algo sobre "Verifique os Cupons de Desconto no APP (ex: CUPOM10, GANHE15) para o preço cair ainda mais!".
        4. O texto DEVE ser curto para leitura rápida no celular.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Erro na IA: {e}")
        return f"🔥 OFERTA SURREAL: {product_name}!\n\n❌ De: R$ {original_price}\n✅ Por apenas: R$ {discount_price}\n\n🎟️ Aplique cupons de Frete Grátis ou Desconto no carrinho!\n\nAproveite antes que esgote! 👇"
