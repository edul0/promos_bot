import random
import requests
import os
from urllib.parse import urlencode, quote

# ID de afiliado - nunca expira!
ML_MATT_TOOL = os.getenv("ML_MATT_TOOL", "82883927")
ML_MATT_WORD = os.getenv("ML_MATT_WORD", "matoscarlos20220825095337")

def generate_ml_affiliate_link(product_url):
    """
    Adiciona parâmetros de rastreamento de afiliado a qualquer URL do ML.
    """
    separator = "&" if "?" in product_url else "?"
    params = urlencode({
        "matt_tool": ML_MATT_TOOL,
        "matt_word": ML_MATT_WORD
    })
    return f"{product_url}{separator}{params}"

def make_search_url(search_term):
    """
    Gera um link de busca do ML com o termo.
    Links de busca SEMPRE funcionam, diferente de links de produto que podem sair do ar.
    """
    encoded = quote(search_term)
    return f"https://lista.mercadolivre.com.br/{encoded}"

def fix_image_url(thumbnail):
    """
    Converte thumbnail pequena do ML em imagem grande.
    """
    if not thumbnail:
        return ""
    image = thumbnail.replace("-I.jpg", "-F.jpg")
    image = image.replace("-I.webp", "-F.jpg")
    if image.startswith("http://"):
        image = image.replace("http://", "https://")
    return image

# Catálogo de ofertas reais - com links de BUSCA (nunca quebram!)
CATALOGO_PRODUTOS = [
    {
        "name": "Smart TV Samsung 55\" Crystal UHD 4K",
        "category": "TVs",
        "original_price": "3499.00",
        "discount_price": "2499.00",
        "search_term": "Smart TV Samsung 55 Crystal UHD 4K"
    },
    {
        "name": "iPhone 15 128GB",
        "category": "Celulares",
        "original_price": "5999.00",
        "discount_price": "4699.00",
        "search_term": "iPhone 15 128GB"
    },
    {
        "name": "PlayStation 5 Slim 1TB",
        "category": "Videogames",
        "original_price": "4499.00",
        "discount_price": "3799.00",
        "search_term": "PlayStation 5 Slim 1TB"
    },
    {
        "name": "Notebook Lenovo IdeaPad 3i Core i5 8GB 256GB SSD",
        "category": "Notebooks",
        "original_price": "3799.00",
        "discount_price": "2899.00",
        "search_term": "Notebook Lenovo IdeaPad 3i Core i5"
    },
    {
        "name": "Fone de Ouvido JBL Tune 520BT Bluetooth",
        "category": "Fones de Ouvido",
        "original_price": "349.00",
        "discount_price": "219.00",
        "search_term": "JBL Tune 520BT Bluetooth"
    },
    {
        "name": "Echo Dot 5ª Geração Amazon com Alexa",
        "category": "Smart Home",
        "original_price": "449.00",
        "discount_price": "299.00",
        "search_term": "Echo Dot 5 geração Alexa"
    },
    {
        "name": "Airfryer Philips Walita 4.1L",
        "category": "Eletrodomésticos",
        "original_price": "599.00",
        "discount_price": "379.00",
        "search_term": "Airfryer Philips Walita"
    },
    {
        "name": "Samsung Galaxy S24 Ultra 256GB",
        "category": "Celulares",
        "original_price": "8999.00",
        "discount_price": "6499.00",
        "search_term": "Samsung Galaxy S24 Ultra 256GB"
    },
    {
        "name": "Monitor Gamer LG UltraGear 27\" 144Hz IPS",
        "category": "Monitores",
        "original_price": "1999.00",
        "discount_price": "1399.00",
        "search_term": "Monitor LG UltraGear 27 144Hz"
    },
    {
        "name": "Kindle 11ª Geração 16GB",
        "category": "Leitores Digitais",
        "original_price": "549.00",
        "discount_price": "399.00",
        "search_term": "Kindle 11 geração 16GB"
    },
    {
        "name": "Xbox Series S 512GB",
        "category": "Videogames",
        "original_price": "2699.00",
        "discount_price": "1999.00",
        "search_term": "Xbox Series S 512GB"
    },
    {
        "name": "Teclado Mecânico Redragon Kumara RGB",
        "category": "Periféricos Gamer",
        "original_price": "299.00",
        "discount_price": "189.00",
        "search_term": "Teclado Mecânico Redragon Kumara RGB"
    },
    {
        "name": "Mouse Gamer Logitech G502 HERO",
        "category": "Periféricos Gamer",
        "original_price": "399.00",
        "discount_price": "249.00",
        "search_term": "Mouse Logitech G502 HERO"
    },
    {
        "name": "SSD Kingston NV2 1TB NVMe M.2",
        "category": "Armazenamento",
        "original_price": "499.00",
        "discount_price": "339.00",
        "search_term": "SSD Kingston NV2 1TB NVMe"
    },
    {
        "name": "Aspirador Robô Xiaomi S10+",
        "category": "Smart Home",
        "original_price": "2999.00",
        "discount_price": "2199.00",
        "search_term": "Aspirador Robô Xiaomi S10"
    },
    {
        "name": "Smartwatch Samsung Galaxy Watch 6 40mm",
        "category": "Relógios Inteligentes",
        "original_price": "1999.00",
        "discount_price": "1499.00",
        "search_term": "Samsung Galaxy Watch 6 40mm"
    },
    {
        "name": "Cadeira Gamer ThunderX3 EC3",
        "category": "Cadeiras Gamer",
        "original_price": "1299.00",
        "discount_price": "899.00",
        "search_term": "Cadeira Gamer ThunderX3 EC3"
    },
    {
        "name": "Tablet Samsung Galaxy Tab A9 64GB",
        "category": "Tablets",
        "original_price": "1499.00",
        "discount_price": "1099.00",
        "search_term": "Tablet Samsung Galaxy Tab A9 64GB"
    },
    {
        "name": "Webcam Logitech C920s Full HD 1080p",
        "category": "Acessórios PC",
        "original_price": "549.00",
        "discount_price": "379.00",
        "search_term": "Webcam Logitech C920s Full HD"
    },
    {
        "name": "Caixa de Som JBL Flip 6 Bluetooth",
        "category": "Caixas de Som",
        "original_price": "899.00",
        "discount_price": "649.00",
        "search_term": "JBL Flip 6 Bluetooth"
    },
]

def get_ml_promotions():
    """
    Busca produtos do ML. Tenta a API primeiro.
    Se bloqueado, usa o catálogo curado com links de busca (que nunca quebram).
    """
    queries = [
        "Placa de video", "Smartphone Samsung", "Smart TV 4K", "Notebook gamer",
        "Fone bluetooth JBL", "SSD 1TB NVMe", "Monitor gamer 144hz",
        "Teclado mecanico RGB", "Mouse gamer", "PlayStation 5",
        "Airfryer", "Echo Dot Alexa", "Kindle", "Xbox Series"
    ]
    query = random.choice(queries)
    
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={query}&limit=20"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
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
    
    # === TENTA A API OFICIAL PRIMEIRO ===
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"ML API Status: {response.status_code} para query '{query}'")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if results:
                new_products = [p for p in results if p.get("id", "") not in sent_ids]
                if not new_products:
                    try:
                        open(history_file, "w").close()
                    except Exception:
                        pass
                    new_products = results
                    
                product = random.choice(new_products)
                
                price = product.get("price", 0)
                original_price = product.get("original_price") or (price * 1.15)
                thumbnail = product.get("thumbnail", "")
                image_url = fix_image_url(thumbnail)
                permalink = product.get("permalink", "")
                affiliate_link = generate_ml_affiliate_link(permalink)
                
                save_history(product.get("id", ""))
                print(f"[API] Produto: {product.get('title')}")
                
                return [{
                    "name": product.get("title", "Produto"),
                    "category": query,
                    "original_price": f"{original_price:.2f}",
                    "discount_price": f"{price:.2f}",
                    "image_url": image_url,
                    "affiliate_link": affiliate_link
                }]
    except Exception as e:
        print(f"ML API erro: {e}")
    
    # === FALLBACK: CATÁLOGO COM LINKS DE BUSCA ===
    print("Usando catálogo curado com links de busca")
    
    unused = [p for p in CATALOGO_PRODUTOS if p["name"] not in sent_ids]
    if not unused:
        try:
            open(history_file, "w").close()
        except Exception:
            pass
        unused = CATALOGO_PRODUTOS
    
    chosen = random.choice(unused)
    save_history(chosen["name"])
    
    # Gera link de BUSCA com afiliado (nunca quebra!)
    search_url = make_search_url(chosen["search_term"])
    affiliate_link = generate_ml_affiliate_link(search_url)
    
    print(f"[CATALOGO] Produto: {chosen['name']}")
    print(f"[CATALOGO] Link: {affiliate_link}")
    
    return [{
        "name": chosen["name"],
        "category": chosen["category"],
        "original_price": chosen["original_price"],
        "discount_price": chosen["discount_price"],
        "image_url": "",  # Sem imagem no fallback, será enviado como texto
        "affiliate_link": affiliate_link
    }]
