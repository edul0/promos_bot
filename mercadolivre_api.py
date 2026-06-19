import random
import requests
import os
from urllib.parse import urlencode

# Método SIMPLES: só precisa do ID de afiliado, sem cookie, sem API, sem expiração!
ML_MATT_TOOL = os.getenv("ML_MATT_TOOL", "82883927")
ML_MATT_WORD = os.getenv("ML_MATT_WORD", "matoscarlos20220825095337")

def generate_ml_affiliate_link(product_url):
    """
    Gera link de afiliado adicionando os parâmetros de rastreamento.
    Não precisa de Cookie, não precisa de API, não expira NUNCA!
    """
    separator = "&" if "?" in product_url else "?"
    params = urlencode({
        "matt_tool": ML_MATT_TOOL,
        "matt_word": ML_MATT_WORD
    })
    return f"{product_url}{separator}{params}"

def fix_image_url(thumbnail):
    """
    Converte thumbnail pequena do ML em imagem grande.
    -F.jpg é o formato que retorna a imagem completa.
    """
    if not thumbnail:
        return ""
    image = thumbnail.replace("-I.jpg", "-F.jpg")
    image = image.replace("-I.webp", "-F.jpg")
    if image.startswith("http://"):
        image = image.replace("http://", "https://")
    return image

# Catálogo de produtos reais do Mercado Livre com imagens verificadas
CATALOGO_PRODUTOS = [
    {
        "name": "Smart TV Samsung 55\" Crystal UHD 4K",
        "category": "TVs",
        "original_price": "3499.00",
        "discount_price": "2499.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_895398-MLA45642874100_042021-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/smart-tv-samsung-55-crystal-uhd-4k/p/MLB20256257"
    },
    {
        "name": "iPhone 15 128GB Apple",
        "category": "Celulares",
        "original_price": "5999.00",
        "discount_price": "4699.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_881731-MLU75417033527_042024-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/apple-iphone-15-128-gb-preto/p/MLB22024109"
    },
    {
        "name": "PlayStation 5 Slim 1TB Sony",
        "category": "Videogames",
        "original_price": "4499.00",
        "discount_price": "3799.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_907072-MLU74005917498_012024-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/playstation-5-slim-1tb/p/MLB22419545"
    },
    {
        "name": "Notebook Lenovo IdeaPad 3i Intel Core i5 8GB 256GB SSD",
        "category": "Notebooks",
        "original_price": "3799.00",
        "discount_price": "2899.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_917484-MLU72092769647_102023-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/notebook-lenovo-ideapad-3i-core-i5/p/MLB21992367"
    },
    {
        "name": "Fone de Ouvido JBL Tune 520BT Bluetooth",
        "category": "Fones de Ouvido",
        "original_price": "349.00",
        "discount_price": "219.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_938789-MLU72753652004_112023-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/jbl-tune-520bt-bluetooth/p/MLB22119887"
    },
    {
        "name": "Echo Dot 5ª Geração Amazon Alexa",
        "category": "Smart Home",
        "original_price": "449.00",
        "discount_price": "299.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_671189-MLU72434927629_102023-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/echo-dot-5-geracao-alexa/p/MLB20953083"
    },
    {
        "name": "Airfryer Philips Walita 4.1L",
        "category": "Eletrodomésticos",
        "original_price": "599.00",
        "discount_price": "379.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_706105-MLU72262989703_102023-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/airfryer-philips-walita/p/MLB19697498"
    },
    {
        "name": "Samsung Galaxy S24 Ultra 256GB",
        "category": "Celulares",
        "original_price": "8999.00",
        "discount_price": "6499.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_738498-MLU75416971707_042024-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/samsung-galaxy-s24-ultra-256gb/p/MLB22423901"
    },
    {
        "name": "Monitor Gamer LG UltraGear 27\" 144Hz IPS",
        "category": "Monitores",
        "original_price": "1999.00",
        "discount_price": "1399.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_840498-MLU72310379747_102023-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/monitor-gamer-lg-ultragear-27/p/MLB19936757"
    },
    {
        "name": "Kindle 11ª Geração Amazon 16GB",
        "category": "Leitores Digitais",
        "original_price": "549.00",
        "discount_price": "399.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_937012-MLU72092769797_102023-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/kindle-11-geracao-16gb/p/MLB21088089"
    },
    {
        "name": "Xbox Series S 512GB Microsoft",
        "category": "Videogames",
        "original_price": "2699.00",
        "discount_price": "1999.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_631740-MLA47951084501_102021-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/xbox-series-s-512gb/p/MLB17752068"
    },
    {
        "name": "Teclado Mecânico Redragon Kumara RGB",
        "category": "Periféricos Gamer",
        "original_price": "299.00",
        "discount_price": "189.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_918938-MLU69744408485_062023-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/teclado-mecanico-redragon-kumara/p/MLB15199498"
    },
    {
        "name": "Mouse Gamer Logitech G502 HERO",
        "category": "Periféricos Gamer",
        "original_price": "399.00",
        "discount_price": "249.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_764703-MLA42608061495_072020-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/mouse-gamer-logitech-g502-hero/p/MLB15089498"
    },
    {
        "name": "SSD Kingston NV2 1TB NVMe M.2",
        "category": "Armazenamento",
        "original_price": "499.00",
        "discount_price": "339.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_896889-MLU70282284189_072023-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/ssd-kingston-nv2-1tb-nvme/p/MLB20631419"
    },
    {
        "name": "Aspirador Robô Xiaomi S10+",
        "category": "Smart Home",
        "original_price": "2999.00",
        "discount_price": "2199.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_683524-MLU74005917398_012024-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/aspirador-robo-xiaomi-s10/p/MLB22424501"
    },
    {
        "name": "Smartwatch Samsung Galaxy Watch 6 40mm",
        "category": "Relógios Inteligentes",
        "original_price": "1999.00",
        "discount_price": "1499.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_738121-MLU72310379697_102023-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/samsung-galaxy-watch-6/p/MLB21986967"
    },
    {
        "name": "Cadeira Gamer ThunderX3 EC3 Preta",
        "category": "Cadeiras Gamer",
        "original_price": "1299.00",
        "discount_price": "899.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_602189-MLU69744408385_062023-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/cadeira-gamer-thunderx3-ec3/p/MLB18855269"
    },
    {
        "name": "Tablet Samsung Galaxy Tab A9 64GB",
        "category": "Tablets",
        "original_price": "1499.00",
        "discount_price": "1099.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_649524-MLU74005917448_012024-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/samsung-galaxy-tab-a9/p/MLB22423001"
    },
    {
        "name": "Webcam Logitech C920s Full HD 1080p",
        "category": "Acessórios PC",
        "original_price": "549.00",
        "discount_price": "379.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_726303-MLA42608061395_072020-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/webcam-logitech-c920s-full-hd/p/MLB15427498"
    },
    {
        "name": "Caixa de Som JBL Flip 6 Bluetooth",
        "category": "Caixas de Som",
        "original_price": "899.00",
        "discount_price": "649.00",
        "image_url": "https://http2.mlstatic.com/D_NQ_NP_789538-MLU72753652104_112023-F.jpg",
        "product_url": "https://www.mercadolivre.com.br/jbl-flip-6-bluetooth/p/MLB20097267"
    },
]

def get_ml_promotions():
    """
    Busca produtos do ML. Tenta a API primeiro.
    Se bloqueado, usa o catálogo curado de produtos reais.
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
    
    # === FALLBACK: CATÁLOGO CURADO ===
    print("Usando catálogo curado de produtos")
    
    unused = [p for p in CATALOGO_PRODUTOS if p["name"] not in sent_ids]
    if not unused:
        try:
            open(history_file, "w").close()
        except Exception:
            pass
        unused = CATALOGO_PRODUTOS
    
    chosen = random.choice(unused)
    save_history(chosen["name"])
    
    print(f"[CATALOGO] Produto: {chosen['name']}")
    
    return [{
        "name": chosen["name"],
        "category": chosen["category"],
        "original_price": chosen["original_price"],
        "discount_price": chosen["discount_price"],
        "image_url": chosen["image_url"],
        "affiliate_link": generate_ml_affiliate_link(chosen["product_url"])
    }]
