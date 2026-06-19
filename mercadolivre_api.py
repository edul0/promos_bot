import random
from config import ML_APP_ID, ML_CLIENT_SECRET

def get_ml_promotions():
    """
    Busca promoções no Mercado Livre.
    COMO AS CHAVES AINDA NÃO FORAM CONFIGURADAS, ESTE É UM MOCK (DADOS FALSOS) PARA TESTAR O BOT.
    """
    if not ML_APP_ID or not ML_CLIENT_SECRET:
        print("⚠️ Chaves do Mercado Livre não configuradas. Usando dados de teste (Mock).")
        
        mock_products = [
            {
                "name": "Smart TV 55 polegadas 4K Samsung",
                "category": "TVs e Eletrônicos",
                "original_price": "3499.00",
                "discount_price": "2499.00",
                "image_url": "https://http2.mlstatic.com/D_NQ_NP_895398-MLA45642874100_042021-O.webp",
                "affiliate_link": "https://mercadolivre.com.br/sec/teste_afiliado_1"
            },
            {
                "name": "Smartphone Poco X6 Pro 5G 256GB",
                "category": "Celulares",
                "original_price": "2199.00",
                "discount_price": "1799.00",
                "image_url": "https://http2.mlstatic.com/D_NQ_NP_794270-MLA74070054707_012024-O.webp",
                "affiliate_link": "https://mercadolivre.com.br/sec/teste_afiliado_2"
            }
        ]
        return [random.choice(mock_products)]
    
    # Futura implementação real da API do Mercado Livre
    # ...
    return []
