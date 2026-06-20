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
from shopee_api import get_shopee_promotion
from ml_oauth import get_authorization_url, exchange_code, kv_get, kv_set
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
    # Banner de cupom/oferta quando há desconto real (preço atual < original)
    deal_banner = ""
    try:
        op = float(product.get('original_price') or 0)
        dp = float(product.get('discount_price') or 0)
        if op > dp > 0:
            pct = round((1 - dp / op) * 100)
            if pct >= 5:
                deal_banner = f"🎟️ CUPOM / OFERTA: {pct}% OFF!\n\n"
    except Exception:
        pass

    final_message = f"{deal_banner}{ad_text}\n\n🛒 Compre aqui: {product['affiliate_link']}"

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


@app.route('/api/cats')
def cats():
    """
    Explorador de categorias do ML para achar IDs (ex.: TCG Pokémon).
    Uso: /api/cats?id=MLB1132   ou   /api/cats?id=MLB1132&q=pokemon
    """
    from ml_oauth import get_valid_access_token
    token = get_valid_access_token()
    cat_id = request.args.get("id", "MLB1132")
    q = (request.args.get("q") or "").lower()
    headers = {"User-Agent": "Mozilla/5.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def get_children(cid):
        try:
            r = requests.get(f"https://api.mercadolibre.com/categories/{cid}", headers=headers, timeout=10)
            if r.status_code != 200:
                return None, []
            d = r.json()
            return d.get("name", ""), [(c["id"], c["name"]) for c in d.get("children_categories", [])]
        except Exception as e:
            return f"erro: {e}", []

    nome, filhos = get_children(cat_id)
    resultado = {"categoria": cat_id, "nome": nome, "filhos": [{"id": i, "nome": n} for i, n in filhos]}

    if q:
        achados = []
        for i, n in filhos:
            if q in n.lower():
                achados.append({"id": i, "nome": n})
            # desce mais um nível procurando o termo
            _, netos = get_children(i)
            for gi, gn in netos:
                if q in gn.lower():
                    achados.append({"id": gi, "nome": gn})
        resultado["achados"] = achados
    return jsonify(resultado)


@app.route('/api/ml_debug')
def ml_debug():
    """Diagnóstico: mostra se há token e o que a API de busca do ML responde."""
    from ml_oauth import get_valid_access_token, KV_URL, KV_TOKEN
    # Lista os nomes de variáveis relacionadas a KV/Redis que a Vercel injetou
    # (só os nomes, nunca os valores secretos)
    kv_vars = sorted([
        k for k in os.environ
        if any(t in k.upper() for t in ("KV_", "UPSTASH", "REDIS"))
    ])
    token = get_valid_access_token()
    info = {
        "kv_configurado": bool(KV_URL and KV_TOKEN),
        "variaveis_kv_detectadas": kv_vars,
        "ml_secret_configurado": bool(os.getenv("ML_CLIENT_SECRET")),
        "tem_token": bool(token),
    }
    if not token:
        info["conclusao"] = "Sem token. KV vazio ou ML_CLIENT_SECRET ausente."
        return jsonify(info)

    # Testa vários endpoints para ver quais ainda respondem com o token.
    # 403 = bloqueado; 200 = ok; 404 = liberado mas id inexistente (serve p/ saber se abre).
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"}
    endpoints = {
        "users_me": "https://api.mercadolibre.com/users/me",
        "search": "https://api.mercadolibre.com/sites/MLB/search?q=jbl&limit=1",
        "item_real": "https://api.mercadolibre.com/items/MLB1234567890",
        "highlights": "https://api.mercadolibre.com/highlights/MLB/category/MLB1055",
    }
    testes = {}
    for nome, u in endpoints.items():
        try:
            r = requests.get(u, headers=headers, timeout=10)
            testes[nome] = {"status": r.status_code, "resp": r.text[:200]}
        except Exception as e:
            testes[nome] = {"erro": str(e)}
    info["testes"] = testes

    # Cadeia real: highlights -> pega 1º id -> busca o produto/item completo
    # para descobrirmos o formato exato (preço, imagem, permalink).
    try:
        h = requests.get(
            "https://api.mercadolibre.com/highlights/MLB/category/MLB1055",
            headers=headers, timeout=10,
        ).json()
        first = h.get("content", [{}])[0]
        pid = first.get("id")
        ptype = first.get("type")
        info["produto_id"] = pid
        info["produto_type"] = ptype
        if pid:
            prod = requests.get(
                f"https://api.mercadolibre.com/products/{pid}",
                headers=headers, timeout=10,
            )
            info["products_status"] = prod.status_code
            info["products_resp"] = prod.text[:1500]
            it = requests.get(
                f"https://api.mercadolibre.com/items/{pid}",
                headers=headers, timeout=10,
            )
            info["items_status"] = it.status_code
            info["items_resp"] = it.text[:600]
    except Exception as e:
        info["cadeia_erro"] = str(e)
    return jsonify(info)


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

    from ml_oauth import save_tokens
    resultado = {"status": "sucesso"}

    # 1) Troca o code pelos tokens
    try:
        token_data = exchange_code(code, get_redirect_uri())
    except Exception as e:
        return jsonify({"status": "erro", "motivo": f"Falha ao trocar o code: {e}"}), 500

    # 2) Testa a API de busca do ML JÁ com o token recém-obtido (de-risk)
    try:
        rt = requests.get(
            "https://api.mercadolibre.com/sites/MLB/search?q=jbl%20flip%206&limit=1",
            headers={"Authorization": f"Bearer {token_data['access_token']}", "User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resultado["busca_status"] = rt.status_code
        resultado["busca_resposta"] = rt.text[:600]
    except Exception as e:
        resultado["busca_erro"] = str(e)

    # 3) Tenta salvar no KV
    try:
        save_tokens(token_data)
        resultado["tokens_salvos"] = True
    except Exception as e:
        resultado["tokens_salvos"] = False
        resultado["kv_erro"] = str(e)

    return jsonify(resultado)

@app.route('/api/cron')
def trigger_cron():
    """
    Endpoint chamado pela Vercel Cron ou manualmente para disparar promoção.
    Alterna automaticamente entre Mercado Livre e Shopee a cada chamada.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return jsonify({"error": "Chaves do Telegram não configuradas no ambiente."}), 500

    # Alterna entre fontes: ML → Shopee → ML → Shopee...
    last_source = kv_get("last_promo_source") or "shopee"
    use_shopee = (last_source == "ml")

    produto = None

    if use_shopee:
        produto = get_shopee_promotion()
        if produto:
            kv_set("last_promo_source", "shopee")
        else:
            print("[CRON] Shopee sem resultado, caindo para ML")

    if not produto:
        ml_promos = get_ml_promotions()
        produto = ml_promos[0] if ml_promos else None
        if produto:
            kv_set("last_promo_source", "ml")

    if not produto:
        return jsonify({"status": "erro", "motivo": "Nenhuma promoção encontrada (ML e Shopee)"}), 500

    asyncio.run(send_promotion_to_telegram(produto))

    return jsonify({
        "status": "sucesso",
        "fonte": produto.get("source", "ml"),
        "produto_enviado": produto["name"],
        "imagem": produto.get("image_url", "sem imagem"),
        "link_afiliado": produto["affiliate_link"]
    })

# Necessário para rodar localmente com `python api/index.py`
if __name__ == '__main__':
    app.run(debug=True, port=5000)
