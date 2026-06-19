import random
from config import SHOPEE_APP_ID, SHOPEE_APP_SECRET

def get_shopee_promotions():
    """
    Busca promoções na Shopee. 
    COMO AS CHAVES AINDA NÃO FORAM CONFIGURADAS, ESTE É UM MOCK (DADOS FALSOS) PARA TESTAR O BOT.
    """
    if not SHOPEE_APP_ID or not SHOPEE_APP_SECRET:
        print("⚠️ Chaves da Shopee não configuradas. Usando dados de teste (Mock).")
        
        mock_products = [
            {
                "name": "Box Booster Pokémon TCG Escarlate e Violeta 151",
                "category": "Cartas Pokémon",
                "original_price": "899.90",
                "discount_price": "649.90",
                "image_url": "https://http2.mlstatic.com/D_NQ_NP_603831-MLU73100693998_112023-O.webp",
                "affiliate_link": "https://shope.ee/link_de_teste_1"
            },
            {
                "name": "Placa de Vídeo RTX 4060 Ti 8GB",
                "category": "Peças de PC",
                "original_price": "2999.00",
                "discount_price": "2399.00",
                "image_url": "https://http2.mlstatic.com/D_NQ_NP_908233-MLU72688048227_112023-O.webp",
                "affiliate_link": "https://shope.ee/link_de_teste_2"
            }
        ]
        return [random.choice(mock_products)]
    
    # Futura implementação real da API da Shopee
    # ...
    return []
