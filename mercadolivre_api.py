import random
import requests
import os
from urllib.parse import urlencode

# Método SIMPLES: só precisa do ID de afiliado, sem cookie, sem API, sem expiração!
ML_MATT_TOOL = os.getenv("ML_MATT_TOOL", "82883927")
ML_MATT_WORD = os.getenv("ML_MATT_WORD", "matoscarlos20220825095337")

def generate_ml_affiliate_link(product_url):
    """
    Gera link de afiliado simplesmente adicionando os parâmetros de rastreamento.
    Não precisa de Cookie, não precisa de API, não expira NUNCA!
    """
    separator = "&" if "?" in product_url else "?"
    params = urlencode({
        "matt_tool": ML_MATT_TOOL,
        "matt_word": ML_MATT_WORD
    })
    return f"{product_url}{separator}{params}"

def get_ml_promotions():
    """
    Busca produtos reais em alta no Mercado Livre e converte para link de afiliado.
    """
    queries = [
        "Placa de video", "Smartphone", "Smart TV 4K", "Notebook gamer",
        "Cartas Pokemon TCG", "Fone bluetooth", "SSD 1TB", "Monitor gamer",
        "Teclado mecanico", "Mouse gamer", "Webcam", "Cadeira gamer",
        "Tablet", "Smartwatch", "Console videogame"
    ]
    query = random.choice(queries)
    
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={query}&limit=20"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # Sistema Anti-Repetição
    history_file = "/tmp/ml_history.txt"
    try:
        with open(history_file, "r") as f:
            sent_ids = f.read().splitlines()
    except FileNotFoundError:
        sent_ids = []
        
    def save_history(product_id):
        try:
            with open(history_file, "a") as f:
                f.write(f"{product_id}\n")
        except Exception:
            pass
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"ML API retornou status {response.status_code}, tentando outra query...")
            # Tenta com outra query antes de desistir
            query2 = random.choice([q for q in queries if q != query])
            url2 = f"https://api.mercadolibre.com/sites/MLB/search?q={query2}&limit=20"
            response = requests.get(url2, headers=headers)
            if response.status_code != 200:
                return []
            
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            return []
        
        # Filtra produtos já enviados
        new_products = [p for p in results if p.get("id", "") not in sent_ids]
        if not new_products:
            # Se todos já foram enviados, limpa o histórico e usa todos
            try:
                open(history_file, "w").close()
            except Exception:
                pass
            new_products = results
            
        product = random.choice(new_products)
        
        price = product.get("price", 0)
        original_price = product.get("original_price") or (price * 1.15)
        
        thumbnail = product.get("thumbnail", "")
        # Converte thumbnail pequena para imagem grande
        image_url = thumbnail.replace("-I.jpg", "-O.jpg") if thumbnail else ""
        
        permalink = product.get("permalink", "")
        affiliate_link = generate_ml_affiliate_link(permalink)
        
        # Salva no histórico
        save_history(product.get("id", ""))
        
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
