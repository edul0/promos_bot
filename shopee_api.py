"""
Integração com o Feed de Produto da Shopee Afiliados.
Foco: Cartas Pokémon TCG + Periféricos e Peças de PC.

Configurar na Vercel:
    SHOPEE_FEED_URL_1  -> link do feed "Shopee Oficial BR"
    SHOPEE_FEED_URL_2  -> link do feed "Shopee Brasil"
"""
import os
import csv
import io
import random
import requests

SHOPEE_FEED_URLS = [
    u for u in [
        os.getenv("SHOPEE_FEED_URL_1", ""),
        os.getenv("SHOPEE_FEED_URL_2", ""),
    ] if u
]

# Shopee: foco em Pokémon TCG e peças/periféricos de PC
CATEGORY_FILTERS = {
    "Cartas Pokémon TCG": [
        "pokemon", "pokémon", "tcg", "carta pokemon", "booster pokemon",
        "copag pokemon", "pikachu", "mewtwo", "charizard", "eevee",
        "gengar", "umbreon", "vstar", "vmax",
    ],
    "Periféricos e Peças de PC": [
        "ssd", "nvme", "hdd", "memória ram", "ram ddr", "placa de vídeo",
        "placa mae", "placa mãe", "processador", "cooler", "water cooler",
        "gabinete", "fonte atx", "mouse gamer", "teclado gamer",
        "teclado mecânico", "monitor gamer", "monitor 144hz", "monitor 165hz",
        "headset gamer", "webcam", "mousepad gamer", "hub usb",
    ],
}

MIN_DISCOUNT_PCT = 10


def _detect_columns(header_row):
    h = [c.strip().lower() for c in header_row]

    def find(*candidates):
        for c in candidates:
            for i, col in enumerate(h):
                if c in col:
                    return i
        return None

    return {
        "name":     find("item_name", "name", "produto", "title"),
        "price":    find("item_price", "sale_price", "price", "preco", "preço"),
        "original": find("original_price", "market_price", "preco_original"),
        "image":    find("item_image", "image", "imagem", "img"),
        "url":      find("item_url", "affiliate_link", "url", "link"),
        "category": find("item_category", "category", "categoria"),
        "discount": find("discount", "desconto"),
        "sales":    find("item_sales", "sold", "sales", "vendas"),
    }


def _parse_feed(url):
    try:
        r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            print(f"[SHOPEE] Feed retornou {r.status_code}")
            return []

        content = r.content.decode("utf-8-sig", errors="replace")
        sample = content[:2000]
        delimiter = "\t" if sample.count("\t") > sample.count(",") else ","
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        rows = list(reader)
        if not rows:
            return []

        cols = _detect_columns(rows[0])
        print(f"[SHOPEE] Colunas detectadas: { {k: v for k, v in cols.items() if v is not None} }")

        products = []
        for row in rows[1:]:
            if len(row) < 3:
                continue

            def g(key):
                idx = cols.get(key)
                return row[idx].strip() if idx is not None and idx < len(row) else ""

            name     = g("name")
            price    = g("price")
            original = g("original")
            image    = g("image")
            url_link = g("url")
            category = g("category")
            discount = g("discount")
            sales    = g("sales")

            if not name or not url_link:
                continue

            try:
                p = float(price.replace(",", ".")) if price else 0
                o = float(original.replace(",", ".")) if original else 0
                disc_str = discount.replace("%", "").strip()
                disc_pct = int(float(disc_str)) if disc_str else 0
                if not disc_pct and p and o and o > p:
                    disc_pct = round((1 - p / o) * 100)
            except Exception:
                p, o, disc_pct = 0, 0, 0

            products.append({
                "name":           name,
                "price":          p,
                "original_price": o,
                "discount_pct":   disc_pct,
                "image_url":      image,
                "affiliate_link": url_link,
                "category_raw":   category,
                "sales":          int(sales) if str(sales).isdigit() else 0,
            })

        print(f"[SHOPEE] {len(products)} produtos no feed")
        return products
    except Exception as e:
        print(f"[SHOPEE] Erro ao parsear feed: {e}")
        return []


def _match_category(product):
    text = f"{product['name']} {product['category_raw']}".lower()
    for cat_name, keywords in CATEGORY_FILTERS.items():
        if any(kw in text for kw in keywords):
            return cat_name
    return None


def get_shopee_promotion(sent_ids=None):
    """
    Retorna 1 produto da Shopee nas categorias de interesse com desconto.
    Retorna None se feeds não configurados ou sem produto elegível.
    """
    if not SHOPEE_FEED_URLS:
        print("[SHOPEE] Env vars SHOPEE_FEED_URL_1/2 não configurados")
        return None

    sent_ids = sent_ids or []
    all_products = []

    urls = SHOPEE_FEED_URLS[:]
    random.shuffle(urls)
    for url in urls:
        products = _parse_feed(url)
        all_products.extend(products)
        if len(all_products) >= 200:
            break

    if not all_products:
        return None

    filtered = []
    for p in all_products:
        cat = _match_category(p)
        if not cat:
            continue
        if p["discount_pct"] < MIN_DISCOUNT_PCT:
            continue
        if p["affiliate_link"] in sent_ids:
            continue
        p["category"] = cat
        filtered.append(p)

    print(f"[SHOPEE] {len(filtered)} elegíveis (Pokémon TCG + PC)")
    if not filtered:
        return None

    # Ordena por desconto * popularidade, escolhe aleatório entre top 10
    filtered.sort(key=lambda x: x["discount_pct"] * (1 + x["sales"] / 1000), reverse=True)
    chosen = random.choice(filtered[:10])

    op = f"{chosen['original_price']:.2f}" if chosen["original_price"] else ""
    dp = f"{chosen['price']:.2f}" if chosen["price"] else ""

    print(f"[SHOPEE] Escolhido: {chosen['name']} — {chosen['discount_pct']}% OFF")
    return {
        "name":           chosen["name"],
        "category":       chosen["category"],
        "original_price": op,
        "discount_price": dp,
        "image_url":      chosen["image_url"],
        "affiliate_link": chosen["affiliate_link"],
        "source":         "shopee",
    }
