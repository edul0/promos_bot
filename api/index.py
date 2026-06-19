import os
import asyncio
import io
import requests
from flask import Flask, jsonify

# Adiciona o diretório pai ao path para conseguir importar os módulos
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from ai_generator import generate_ad_text
from shopee_api import get_shopee_promotions
from mercadolivre_api import get_ml_promotions
from telegram import Bot

app = Flask(__name__)

async def send_promotion_to_telegram(product):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    ad_text = generate_ad_text(
        product_name=product['name'],
        original_price=product['original_price'],
        discount_price=product['discount_price'],
        category=product['category']
    )
    final_message = f"{ad_text}\n\n🛒 Compre aqui: {product['affiliate_link']}"
    
    try:
        if product.get('image_url'):
            # Baixa a imagem internamente para evitar que o Telegram seja bloqueado pelo ML
            response = requests.get(product['image_url'], headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                photo_bytes = io.BytesIO(response.content)
                photo_bytes.name = "imagem.jpg"  # <-- ATRIBUTO OBRIGATÓRIO PARA O TELEGRAM
                await bot.send_photo(
                    chat_id=TELEGRAM_CHAT_ID,
                    photo=photo_bytes,
                    caption=final_message
                )
            else:
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=final_message)
        else:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=final_message)
        return True
    except Exception as e:
        print(f"Erro na foto: {e}. Enviando como texto...")
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=final_message)
            return True
        except Exception as e2:
            print(f"Erro total: {e2}")
            return False

@app.route('/')
def home():
    return jsonify({"status": "Bot está online! Acesse /api/cron para disparar uma promoção."})

@app.route('/api/cron')
def trigger_cron():
    """
    Este endpoint será chamado pela Vercel ou pelo cron-job.org 
    para disparar as promoções.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return jsonify({"error": "Chaves do Telegram não configuradas no ambiente."}), 500

    promos_enviadas = []
    
    # Busca 1 promoção da Shopee e 1 do ML para evitar spam e timeout na Vercel
    shopee_promos = get_shopee_promotions()
    if shopee_promos:
        asyncio.run(send_promotion_to_telegram(shopee_promos[0]))
        promos_enviadas.append(shopee_promos[0]['name'])
        
    ml_promos = get_ml_promotions()
    if ml_promos:
        asyncio.run(send_promotion_to_telegram(ml_promos[0]))
        promos_enviadas.append(ml_promos[0]['name'])
        
    return jsonify({
        "status": "sucesso", 
        "promocoes_enviadas": promos_enviadas
    })

# Necessário para rodar localmente com `python api/index.py`
if __name__ == '__main__':
    app.run(debug=True, port=5000)
