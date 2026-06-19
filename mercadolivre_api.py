import random
import requests

def get_ml_promotions():
    """
    Busca produtos reais em alta no Mercado Livre.
    """
    queries = ["Placa de video", "Smartphone", "Smart TV", "Notebook", "Cartas Pokemon TCG"]
    query = random.choice(queries)
    
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={query}&limit=10"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if "results" not in data or len(data["results"]) == 0:
            return []
            
        # Pega um produto aleatório dos top 10 resultados
        product = random.choice(data["results"])
        
        # O preço original e o preço com desconto (nem todos tem preço original)
        price = product.get("price", 0)
        original_price = product.get("original_price") or (price * 1.1) # Simula um desconto se não tiver
        
        # Pegar imagem em boa qualidade
        thumbnail = product.get("thumbnail", "")
        image_url = thumbnail.replace("-I.jpg", "-O.jpg") if thumbnail else ""
        
        # Link do produto (o usuário precisará converter para link de afiliado ou usar sua tag)
        permalink = product.get("permalink", "")
        
        return [{
            "name": product.get("title", "Produto"),
            "category": query,
            "original_price": f"{original_price:.2f}",
            "discount_price": f"{price:.2f}",
            "image_url": image_url,
            "affiliate_link": permalink # AQUI DEPOIS PODEMOS ADICIONAR A TAG DE AFILIADO
        }]
        
    except Exception as e:
        print(f"Erro ao buscar no ML: {e}")
        return []
