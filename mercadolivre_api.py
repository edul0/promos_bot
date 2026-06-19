import random
import requests
import os

# Pega o cookie de sessão do ML nas variáveis de ambiente
ML_COOKIE = os.getenv("ML_COOKIE", "")

def generate_ml_affiliate_link(product_url):
    """
    Usa o endpoint interno do ML para gerar o link de afiliado usando o Cookie.
    """
    if not ML_COOKIE:
        return product_url # Retorna o original se não tiver o cookie configurado
        
    url = "https://www.mercadolivre.com.br/affiliate-program/api/v2/affiliates/createLink"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": ML_COOKIE
    }
    payload = {"url": product_url}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("link", product_url)
    except Exception as e:
        print(f"Erro ao gerar link de afiliado: {e}")
        
    return product_url

def get_ml_promotions():
    """
    Busca produtos reais em alta no Mercado Livre e tenta converter para link de afiliado.
    """
    queries = ["Placa de video", "Smartphone", "Smart TV", "Notebook", "Cartas Pokemon TCG"]
    query = random.choice(queries)
    
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={query}&limit=10"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if "results" not in data or len(data["results"]) == 0:
            return []
            
        product = random.choice(data["results"])
        
        price = product.get("price", 0)
        original_price = product.get("original_price") or (price * 1.1)
        
        thumbnail = product.get("thumbnail", "")
        image_url = thumbnail.replace("-I.jpg", "-O.jpg") if thumbnail else ""
        
        permalink = product.get("permalink", "")
        
        # TRANSFORMA NO LINK DE AFILIADO
        affiliate_link = generate_ml_affiliate_link(permalink)
        
        return [{
            "name": product.get("title", "Produto"),
            "category": query,
            "original_price": f"{original_price:.2f}",
            "discount_price": f"{price:.2f}",
            "image_url": image_url,
            "affiliate_link": affiliate_link
        }]
        
    except Exception as e:
        print(f"Erro ao buscar no ML: {e}")
        return []
