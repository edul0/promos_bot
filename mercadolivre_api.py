import random
import json
import requests
import os
from urllib.parse import urlencode, quote

from ml_oauth import get_valid_access_token, kv_get, kv_set
from ml_affiliate import generate_official_affiliate_link

ML_MATT_TOOL = os.getenv("ML_MATT_TOOL", "")
ML_MATT_WORD = os.getenv("ML_MATT_WORD", "")

def generate_ml_affiliate_link(product_url):
    """
    Adiciona parâmetros de rastreamento de afiliado a qualquer URL do ML.
    """
    if not ML_MATT_TOOL or not ML_MATT_WORD:
        return product_url
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

# Categorias do ML (Brasil) p/ os MAIS VENDIDOS via /highlights.
# Formato: id -> (nome, peso, filtro_nome_obrigatorio).
# filtro_nome_obrigatorio: tuple de strings que DEVEM estar no nome do produto (case-insensitive).
# None = sem filtro.
ML_HIGHLIGHT_CATEGORIES = {
    # === DESTAQUE (peso alto) ===
    "MLB3697": ("Fones de Ouvido", 4, None),
    "MLB1132": ("Cartas Colecionáveis / Pokémon", 4, ("pokemon", "pokémon", "tcg")),  # MLB1132 é muito amplo; filtra por nome
    "MLB1648": ("Informática e Peças de PC", 4, None),
    # === GERAIS (peso 1) ===
    "MLB1000": ("Eletrônicos, Áudio e Vídeo", 1, None),
    "MLB1144": ("Games", 1, None),
    "MLB1051": ("Celulares e Telefones", 1, None),
    "MLB1276": ("Esportes e Fitness", 1, None),
    "MLB1039": ("Câmeras e Acessórios", 1, None),
    "MLB5726": ("Eletrodomésticos", 1, None),
    "MLB1574": ("Casa, Móveis e Decoração", 1, None),
}


def _weighted_category_order():
    """Ordena as categorias dando prioridade às de maior peso (destaque)."""
    pool = []
    for cid, (name, weight, name_filter) in ML_HIGHLIGHT_CATEGORIES.items():
        pool.extend([(cid, name, name_filter)] * weight)
    random.shuffle(pool)
    seen, order = set(), []
    for cid, name, name_filter in pool:
        if cid not in seen:
            seen.add(cid)
            order.append((cid, name, name_filter))
    return order


def _passes_name_filter(product_name, name_filter):
    """Retorna True se o produto passa no filtro de nome (ou se não há filtro)."""
    if not name_filter:
        return True
    name_lower = product_name.lower()
    return any(term in name_lower for term in name_filter)


def _ml_headers(token):
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    if token:
        h['Authorization'] = f'Bearer {token}'
    return h


def _build_product_link(product_id):
    """A página de produto do catálogo do ML é /p/{id}. Adiciona o afiliado."""
    return generate_ml_affiliate_link(f"https://www.mercadolivre.com.br/p/{product_id}")


def _best_affiliate_link(product_url, fallback_url):
    """
    Tenta o link OFICIAL (meli.la) via gerador; se falhar (sessão expirada etc.),
    usa o fallback /p/...matt_tool (que ainda carrega a etiqueta de afiliado).
    """
    official = generate_official_affiliate_link(product_url)
    if official:
        print(f"[AFILIADO] meli.la oficial: {official}")
        return official
    return generate_ml_affiliate_link(fallback_url)


def _extract_product_image(data, pid):
    """Acha a melhor imagem num /products/{id} (pictures no topo ou nos pickers)."""
    pics = data.get("pictures") or []
    if pics and pics[0].get("url"):
        return fix_image_url(pics[0]["url"])
    # cai pros pickers: prioriza o thumbnail do próprio id
    pickers = data.get("pickers") or []
    fallback = ""
    for pk in pickers:
        for prod in pk.get("products", []):
            th = prod.get("thumbnail", "")
            if not th:
                continue
            if prod.get("product_id") == pid:
                return fix_image_url(th)
            if not fallback:
                fallback = th
    return fix_image_url(fallback) if fallback else ""


def _fetch_product(token, pid, ptype, cat_name):
    """Busca os detalhes reais (nome, imagem, preço, link) de 1 produto/item."""
    headers = _ml_headers(token)
    try:
        if ptype == "ITEM":
            r = requests.get(f"https://api.mercadolibre.com/items/{pid}", headers=headers, timeout=10)
            if r.status_code != 200:
                return None
            d = r.json()
            price = d.get("price") or 0
            original = d.get("original_price") or 0
            # Estima 15% acima para o "De: R$" se não tiver original
            if price and not original:
                original = round(float(price) * 1.15, 2)
            pics = d.get("pictures") or []
            image = fix_image_url(pics[0]["url"]) if pics else fix_image_url(d.get("thumbnail", ""))
            permalink = d.get("permalink", "")
            real_url = permalink or f"https://www.mercadolivre.com.br/p/{pid}"
            fallback = permalink or f"https://www.mercadolivre.com.br/p/{pid}"
            link = _best_affiliate_link(real_url, fallback)
            return {
                "name": d.get("title", "Produto"),
                "category": cat_name,
                "original_price": f"{original:.2f}" if original else "",
                "discount_price": f"{price:.2f}" if price else "",
                "image_url": image,
                "affiliate_link": link,
            }
        # type PRODUCT (catálogo)
        r = requests.get(f"https://api.mercadolibre.com/products/{pid}", headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        d = r.json()
        bbw = d.get("buy_box_winner") or {}
        price = bbw.get("price") or 0
        original = bbw.get("original_price") or 0
        
        # Ocasionalmente o ML esconde o preço do /products, mas deixa o item_id
        if not price and bbw.get("item_id"):
            try:
                ir = requests.get(f"https://api.mercadolibre.com/items/{bbw['item_id']}", headers=headers, timeout=5)
                if ir.status_code == 200:
                    id_data = ir.json()
                    price = id_data.get("price") or 0
                    original = id_data.get("original_price") or 0
            except:
                pass
                
        # Se buy_box_winner for nulo ou não tiver item_id, busca o preço do produto via /search
        if not price:
            try:
                prod_name = d.get("name", "")
                if prod_name:
                    from urllib.parse import quote
                    q = quote(prod_name)
                    search_r = requests.get(f"https://api.mercadolibre.com/sites/MLB/search?q={q}&limit=1", headers=headers, timeout=5)
                    if search_r.status_code == 200:
                        results = search_r.json().get("results", [])
                        if results:
                            price = results[0].get("price") or 0
                            original = results[0].get("original_price") or 0
            except:
                pass
                
        # Se achou preço mas não tem original, gera um original estimado (15% a mais) para o visual de desconto
        if price and not original:
            original = round(float(price) * 1.15, 2)
        image = _extract_product_image(d, pid)
        if not image:
            return None  # sem imagem não vale a pena (objetivo é promo COM imagem)
        pid_url = f"https://www.mercadolivre.com.br/p/{pid}"
        return {
            "name": d.get("name", "Produto"),
            "category": cat_name,
            "original_price": f"{original:.2f}" if original else "",
            "discount_price": f"{price:.2f}" if price else "",
            "image_url": image,
            "affiliate_link": _best_affiliate_link(pid_url, pid_url),
        }
    except Exception as e:
        print(f"Erro ao buscar produto {pid}: {e}")
        return None


HISTORY_KEY = "ml_sent_ids"
HISTORY_MAX = 40  # guarda os últimos 40 IDs para evitar repetição


def _load_history():
    """Carrega o histórico de IDs enviados do KV."""
    try:
        raw = kv_get(HISTORY_KEY)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return []


def _save_history(sent_ids, new_id):
    """Adiciona new_id ao histórico e persiste no KV."""
    updated = (sent_ids + [new_id])[-HISTORY_MAX:]
    try:
        kv_set(HISTORY_KEY, json.dumps(updated))
    except Exception as e:
        print(f"Erro ao salvar histórico no KV: {e}")
    return updated


def _get_from_highlights(token, sent_ids):
    """Pega os mais vendidos de uma categoria aleatória e monta a promo."""
    headers = _ml_headers(token)
    cats = _weighted_category_order()
    for cat_id, cat_name, name_filter in cats:
        try:
            hr = requests.get(
                f"https://api.mercadolibre.com/highlights/MLB/category/{cat_id}",
                headers=headers, timeout=10,
            )
            if hr.status_code != 200:
                print(f"highlights {cat_id}: status {hr.status_code}")
                continue
            content = hr.json().get("content", [])
            # Prefere itens não enviados antes; senão tenta todos
            candidates = [c for c in content if c.get("id") not in sent_ids] or content
            random.shuffle(candidates)
            for c in candidates[:8]:
                pid, ptype = c.get("id"), c.get("type")
                if not pid:
                    continue
                promo = _fetch_product(token, pid, ptype, cat_name)
                if not promo:
                    continue
                if not _passes_name_filter(promo["name"], name_filter):
                    print(f"[FILTRO] Ignorado ({cat_name}): {promo['name']}")
                    continue
                _save_history(sent_ids, pid)
                print(f"[HIGHLIGHTS] {cat_name}: {promo['name']}")
                return promo
        except Exception as e:
            print(f"Erro highlights {cat_id}: {e}")
            continue
    return None


def get_ml_promotions():
    """
    Busca os MAIS VENDIDOS do ML (API autenticada /highlights + /products).
    Se não houver token ou a API falhar, cai no catálogo curado.
    """
    access_token = get_valid_access_token()

    # Histórico anti-repetição persistido no KV
    sent_ids = _load_history()

    # === API AUTENTICADA: MAIS VENDIDOS ===
    if access_token:
        promo = _get_from_highlights(access_token, sent_ids)
        if promo:
            return [promo]
        print("Highlights não retornou produto; usando catálogo")
    else:
        print("Sem token do ML (autorize em /api/ml_auth); usando catálogo")

    # === FALLBACK: CATÁLOGO COM LINKS DE BUSCA ===
    print("Usando catálogo curado com links de busca")

    unused = [p for p in CATALOGO_PRODUTOS if p["name"] not in sent_ids]
    if not unused:
        unused = CATALOGO_PRODUTOS

    chosen = random.choice(unused)
    _save_history(sent_ids, chosen["name"])

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
        "image_url": "",  # catálogo é texto; a busca de imagem foi bloqueada pelo ML
        "affiliate_link": affiliate_link
    }]
