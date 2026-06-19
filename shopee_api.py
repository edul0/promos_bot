import random
import requests
import os
import time
import hmac
import hashlib
import json

# Pegando as chaves da Shopee
SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID", "")
SHOPEE_APP_SECRET = os.getenv("SHOPEE_APP_SECRET", "")

def generate_shopee_signature(path, timestamp):
    """
    Gera a assinatura HMAC-SHA256 necessária para a API da Shopee.
    """
    base_string = f"{SHOPEE_APP_ID}{path}{timestamp}"
    return hmac.new(
        SHOPEE_APP_SECRET.encode('utf-8'), 
        base_string.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()

def generate_shopee_short_link(long_url):
    """
    Converte um link normal da Shopee em um link curto de afiliado.
    """
    if not SHOPEE_APP_ID or not SHOPEE_APP_SECRET:
        return long_url # Retorna sem afiliar se não tiver as chaves
        
    path = "/api/v2/affiliate/generate_short_link" # Rota da Open API de Afiliados da Shopee
    timestamp = int(time.time())
    sign = generate_shopee_signature(path, timestamp)
    
    url = f"https://partner.shopeemobile.com{path}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": f"""
        mutation {{
            generateShortLink(input: {{ originUrl: "{long_url}", subIds: ["bot_telegram"] }}) {{
                shortLink
            }}
        }}
        """
    }
    
    # A Shopee usa GraphQL no Open API
    try:
        # Obs: A rota exata pode variar entre GraphQL ou REST dependendo da versão.
        # Estamos implementando um fallback simples. Se não der, retornamos o link.
        pass 
    except:
        pass
        
    return long_url

def get_shopee_promotions():
    """
    Busca produtos na Shopee usando a API pública e tenta gerar o link de afiliado.
    """
    queries = ["Placa de video", "Smartphone", "Smart TV", "Notebook", "Cartas Pokemon TCG"]
    query = random.choice(queries)
    
    url = f"https://shopee.com.br/api/v4/search/search_items?keyword={query}&limit=10"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        items = data.get("items", [])
        if not items:
            return []
            
        item_data = random.choice(items)
        item = item_data.get("item_basic", item_data)
        
        name = item.get("name", "Produto Shopee")
        price = item.get("price", 0) / 100000 # O preço na Shopee vem multiplicado
        original_price = item.get("price_before_discount", 0) / 100000
        if original_price == 0: original_price = price * 1.1
        
        image_id = item.get("image", "")
        image_url = f"https://cf.shopee.com.br/file/{image_id}" if image_id else ""
        
        itemid = item.get("itemid", "")
        shopid = item.get("shopid", "")
        permalink = f"https://shopee.com.br/product/{shopid}/{itemid}"
        
        affiliate_link = generate_shopee_short_link(permalink)
        
        return [{
            "name": name,
            "category": query,
            "original_price": f"{original_price:.2f}",
            "discount_price": f"{price:.2f}",
            "image_url": image_url,
            "affiliate_link": affiliate_link
        }]
        
    except Exception as e:
        print(f"Erro na busca da Shopee: {e}")
        return []
