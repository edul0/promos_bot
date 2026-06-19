import os
import asyncio
import io
import requests
from flask import Flask, jsonify, request, redirect

# Adiciona o diretório pai ao path para conseguir importar os módulos
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from ai_generator import generate_ad_text
from mercadolivre_api import get_ml_promotions
from ml_oauth import get_authorization_url, exchange_code
from telegram import Bot

app = Flask(__name__)


def get_redirect_uri():
    """Monta o redirect_uri do OAuth a partir do host atual (sempre https na Vercel)."""
    host = request.headers.get("X-Forwarded-Host") or request.host
    return f"https://{host}/api/ml_callback"

async def send_promotion_to_telegram(product):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    ad_text = generate_ad_text(
        product_name=product['name'],
        original_price=product['original_price'],
        discount_price=product['discount_price'],
        category=product['category']
    )
    final_message = f"{ad_text}\n\n🛒 Compre aqui: {product['affiliate_link']}"
    
    # Telegram limita caption de fotos a 1024 caracteres!
    if len(final_message) > 1024:
        final_message = final_message[:1020] + "..."
    
    image_sent = False
    
    if product.get('image_url'):
        try:
            # Baixa a imagem na Vercel com headers completos
            img_response = requests.get(
                product['image_url'], 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'image/*',
                    'Referer': 'https://www.mercadolivre.com.br/'
                },
                timeout=10
            )
            
            if img_response.status_code == 200 and len(img_response.content) > 1000:
                photo_bytes = io.BytesIO(img_response.content)
                photo_bytes.name = "promo.jpg"
                await bot.send_photo(
                    chat_id=TELEGRAM_CHAT_ID,
                    photo=photo_bytes,
                    caption=final_message
                )
                image_sent = True
                print(f"Foto enviada OK! ({len(img_response.content)} bytes)")
            else:
                print(f"Imagem muito pequena ou erro: status={img_response.status_code}, size={len(img_response.content)}")
        except Exception as e:
            print(f"Erro ao baixar/enviar foto: {e}")
    
    if not image_sent:
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=final_message)
            print("Mensagem enviada como texto (sem foto)")
        except Exception as e:
            print(f"Erro total ao enviar mensagem: {e}")
            return False
    
    return True

@app.route('/')
def home():
    return jsonify({"status": "Bot está online! Acesse /api/cron para disparar uma promoção."})


@app.route('/api/ml_auth')
def ml_auth():
    """Passo 1 do OAuth: redireciona o usuário para autorizar o app no Mercado Livre."""
    redirect_uri = get_redirect_uri()
    return redirect(get_authorization_url(redirect_uri))


@app.route('/api/ml_callback')
def ml_callback():
    """Passo 2 do OAuth: o ML volta aqui com ?code=... -> trocamos por tokens e salvamos."""
    code = request.args.get("code")
    error = request.args.get("error")
    if error:
        return jsonify({"status": "erro", "motivo": error}), 400
    if not code:
        return jsonify({"status": "erro", "motivo": "code ausente na resposta do ML"}), 400

    try:
        exchange_code(code, get_redirect_uri())
        return jsonify({
            "status": "sucesso",
            "mensagem": "Autorização concluída! Tokens salvos no Vercel KV. O bot já pode buscar produtos reais."
        })
    except Exception as e:
        return jsonify({"status": "erro", "motivo": f"Falha ao trocar o code: {e}"}), 500

@app.route('/api/cron')
def trigger_cron():
    """
    Endpoint chamado pela Vercel Cron ou manualmente para disparar promoção.
    Envia apenas 1 promoção do Mercado Livre por vez.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return jsonify({"error": "Chaves do Telegram não configuradas no ambiente."}), 500

    ml_promos = get_ml_promotions()
    
    if not ml_promos:
        return jsonify({"status": "erro", "motivo": "Nenhuma promoção encontrada no ML"}), 500
    
    produto = ml_promos[0]
    asyncio.run(send_promotion_to_telegram(produto))
    
    return jsonify({
        "status": "sucesso", 
        "produto_enviado": produto['name'],
        "imagem": produto.get('image_url', 'sem imagem'),
        "link_afiliado": produto['affiliate_link']
    })

# Necessário para rodar localmente com `python api/index.py`
if __name__ == '__main__':
    app.run(debug=True, port=5000)
