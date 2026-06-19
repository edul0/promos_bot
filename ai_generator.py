import google.generativeai as genai
from config import GEMINI_API_KEY
import random

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_ad_text(product_name, original_price, discount_price, category):
    """
    Usa o Gemini para criar um texto chamativo para Telegram com base nos detalhes do produto.
    Caso a chave da API não esteja configurada, retorna um texto padrão.
    """
    if not GEMINI_API_KEY:
        # Fallback sem IA
        return f"🔥 Promoção em {category} 🔥\n\n{product_name}\nDe: R$ {original_price}\nPor: R$ {discount_price}\n\nAproveite antes que acabe!"

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Você é um copywriter especialista em grupos de promoções no Telegram.
        Crie um texto curto, empolgante, com emojis e muito chamativo para o seguinte produto:
        
        Produto: {product_name}
        Categoria: {category}
        Preço original: R$ {original_price}
        Preço com desconto: R$ {discount_price}
        
        Regras:
        - Não escreva o link (eu vou adicionar no código depois).
        - Use gatilhos mentais de urgência (Ex: 'Corre que acaba rápido', 'Estoque limitado').
        - Seja direto, as pessoas no Telegram querem ler rápido.
        - Não coloque aspas em volta da mensagem.
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erro ao gerar texto com IA: {e}")
        return f"🔥 OFERTA IMPERDÍVEL 🔥\n\n{product_name}\nDe: R$ {original_price}\nPor: R$ {discount_price}"
