import random
import json
import requests
import os
from urllib.parse import urlencode, quote

from ml_oauth import get_valid_access_token, kv_get, kv_set
from ml_affiliate import generate_official_affiliate_link
from offer_history import eligible

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

# Categorias do ML (Brasil) p/ os MAIS VENDIDOS via /highlights.
# Formato: id -> (nome, peso, filtro_nome_obrigatorio).
# filtro_nome_obrigatorio: tuple de strings que DEVEM estar no nome do produto (case-insensitive).
# None = sem filtro.
ML_HIGHLIGHT_CATEGORIES = {
    # === DESTAQUE (peso alto) ===
    "MLB3697": ("Fones de Ouvido", 1, None),
    "MLB1132": ("Cartas Colecionáveis / Pokémon", 1, ("pokemon", "pokémon", "tcg")),  # MLB1132 é muito amplo; filtra por nome
    "MLB1648": ("Informática e Peças de PC", 1, None),
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
    retém o produto quando a sessão não gera um link oficial.
    """
    official = generate_official_affiliate_link(product_url)
    if official:
        print(f"[AFILIADO] meli.la oficial: {official}")
        return official
    # Sem confirmação do gerador da conta, não publica o produto.
    return None


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


def _extract_coupon(item_data):
    """
    Extrai cupom ativo de um item do ML.
    Retorna dict com code, discount_pct, min_value, platform ou {} se não houver.
    Só considera cupom "bom" se tiver >= 5% de desconto ou valor mínimo definido.
    """
    promotions = item_data.get("promotions") or []
    best = {}
    for promo in promotions:
        code = promo.get("code") or promo.get("coupon_code")
        ptype = (promo.get("type") or "").upper()
        if not code or ptype not in ("COUPON", "DEAL", "LOYALTY", "CAMPAIGN"):
            continue

        # Desconto percentual ou fixo
        disc_pct  = promo.get("discount_percentage") or promo.get("rate") or 0
        disc_val  = promo.get("discount_value") or promo.get("amount") or 0
        min_value = promo.get("min_price") or promo.get("minimum_price") or 0

        # Plataforma onde pode ser usado
        scope = (promo.get("scope") or promo.get("channel") or "").lower()
        if "app" in scope:
            platform = "App do Mercado Livre"
        elif "web" in scope:
            platform = "Site do Mercado Livre"
        else:
            platform = "Mercado Livre (app ou site)"

        # Só considera cupom com desconto real (>= 5%)
        try:
            disc_pct = float(disc_pct)
        except Exception:
            disc_pct = 0

        if disc_pct < 5 and not disc_val:
            continue

        if not best or disc_pct > best.get("discount_pct", 0):
            best = {
                "code":         str(code),
                "discount_pct": disc_pct,
                "discount_val": disc_val,
                "min_value":    min_value,
                "platform":     platform,
            }

    return best


def _fetch_product(token, pid, ptype, cat_name):
    """Busca os detalhes reais (nome, imagem, preço, link, cupom) de 1 produto/item."""
    headers = _ml_headers(token)
    try:
        if ptype == "ITEM":
            r = requests.get(f"https://api.mercadolibre.com/items/{pid}", headers=headers, timeout=10)
            if r.status_code != 200:
                return None
            d = r.json()
            price = d.get("price") or 0
            original = d.get("original_price") or 0
            pics = d.get("pictures") or []
            image = fix_image_url(pics[0]["url"]) if pics else fix_image_url(d.get("thumbnail", ""))
            permalink = d.get("permalink", "")
            real_url = permalink or f"https://www.mercadolivre.com.br/p/{pid}"
            link = _best_affiliate_link(real_url, real_url)
            coupon = _extract_coupon(d)
            return {
                "name": d.get("title", "Produto"),
                "category": cat_name,
                "original_price": f"{original:.2f}" if original else "",
                "discount_price": f"{price:.2f}" if price else "",
                "image_url": image,
                "affiliate_link": link,
                "coupon": coupon,
            }
        # type PRODUCT (catálogo)
        r = requests.get(f"https://api.mercadolibre.com/products/{pid}", headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        d = r.json()
        bbw = d.get("buy_box_winner") or {}
        price = bbw.get("price") or 0
        original = bbw.get("original_price") or 0
        
        # Tenta recuperar o preço via item_id do buy_box_winner
        if not price and bbw.get("item_id"):
            try:
                ir = requests.get(f"https://api.mercadolibre.com/items/{bbw['item_id']}", headers=headers, timeout=5)
                if ir.status_code == 200:
                    id_data = ir.json()
                    price = id_data.get("price") or 0
                    original = id_data.get("original_price") or 0
            except Exception:
                pass

        # Fallback: lista os itens do produto e pega o preço do item com mais vendas (sold_quantity)
        if not price:
            try:
                ir = requests.get(f"https://api.mercadolibre.com/products/{pid}/items", headers=headers, timeout=5)
                if ir.status_code == 200:
                    results = ir.json().get("results") or []
                    if results:
                        # Prefere o item com mais vendas (mais representativo do preço real)
                        best = max(results, key=lambda i: i.get("sold_quantity") or 0)
                        price = best.get("price") or 0
                        original = best.get("original_price") or 0
            except Exception:
                pass
                
        image = _extract_product_image(d, pid)
        if not image:
            return None
        pid_url = f"https://www.mercadolivre.com.br/p/{pid}"
        # Tenta buscar cupom do item vencedor do buy_box
        coupon = ""
        if bbw.get("item_id"):
            try:
                ir = requests.get(f"https://api.mercadolibre.com/items/{bbw['item_id']}",
                                   headers=headers, timeout=5)
                if ir.status_code == 200:
                    coupon = _extract_coupon(ir.json())
            except Exception:
                pass
        return {
            "name": d.get("name", "Produto"),
            "category": cat_name,
            "original_price": f"{original:.2f}" if original else "",
            "discount_price": f"{price:.2f}" if price else "",
            "image_url": image,
            "affiliate_link": _best_affiliate_link(pid_url, pid_url),
            "coupon": coupon,
        }
    except Exception as e:
        print(f"Erro ao buscar produto {pid}: {e}")
        return None


HISTORY_KEY = "ml_sent_ids"
LAST_CAT_KEY = "ml_last_cat"
HISTORY_MAX = 60


def _load_history():
    try:
        raw = kv_get(HISTORY_KEY)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return []


def _save_history(sent_ids, new_id, cat_id):
    updated = (sent_ids + [new_id])[-HISTORY_MAX:]
    try:
        kv_set(HISTORY_KEY, json.dumps(updated))
        kv_set(LAST_CAT_KEY, cat_id)
    except Exception as e:
        print(f"Erro ao salvar histórico no KV: {e}")
    return updated


def _load_last_cat():
    try:
        return kv_get(LAST_CAT_KEY) or ""
    except Exception:
        return ""


def _get_from_highlights(token, sent_ids):
    """Pega os mais vendidos de uma categoria diferente da última usada."""
    headers = _ml_headers(token)
    last_cat = _load_last_cat()
    cats = _weighted_category_order()

    # Move a última categoria usada pro final para evitar repetição imediata
    if last_cat:
        cats = [c for c in cats if c[0] != last_cat] + [c for c in cats if c[0] == last_cat]

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
            candidates = [c for c in content if c.get("id")]
            if not candidates:
                print(f"[SKIP] {cat_name}: todos os {len(content)} itens já enviados")
                continue  # pula categoria esgotada, NÃO repete
            random.shuffle(candidates)
            for c in candidates[:8]:
                pid, ptype = c.get("id"), c.get("type")
                if not pid:
                    continue
                promo = _fetch_product(token, pid, ptype, cat_name)
                if not promo:
                    continue
                if not eligible(promo) or not _passes_name_filter(promo["name"], name_filter):
                    print(f"[FILTRO] Ignorado ({cat_name}): {promo['name']}")
                    continue
                promo["_ml_pid"] = pid
                promo["_ml_cat"] = cat_id
                promo["source"] = "ml"
                print(f"[HIGHLIGHTS] {cat_name}: {promo['name']}")
                return promo
        except Exception as e:
            print(f"Erro highlights {cat_id}: {e}")
            continue

    return None


def get_ml_promotions():
    """
    Busca os MAIS VENDIDOS do ML (API autenticada /highlights + /products).
    Sem token ou oferta atual, não publica preços estáticos.
    """
    access_token = get_valid_access_token()

    # Histórico anti-repetição persistido no KV
    sent_ids = _load_history()

    # === API AUTENTICADA: MAIS VENDIDOS ===
    if access_token:
        promo = _get_from_highlights(access_token, sent_ids)
        if promo:
            return [promo]
        print("Highlights não retornou produto; sem oferta atual")
    else:
        print("Sem token do ML (autorize em /api/ml_auth); sem oferta atual")

    # Catálogo fixo desativado: não há preço atual nem anúncio específico.
    return []
