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

# Feed da Shopee costuma trazer discount=0; não exige desconto, mas prioriza quem tem
MIN_DISCOUNT_PCT = 0


def _detect_columns(header_row):
    h = [c.strip().lower() for c in header_row]

    def exact(name):
        for i, col in enumerate(h):
            if col == name:
                return i
        return None

    def find(*candidates, exclude=()):
        for c in candidates:
            for i, col in enumerate(h):
                if c in col and not any(x in col for x in exclude):
                    return i
        return None

    return {
        "name":     exact("title") or exact("item_name") or exact("product_name") or
                    find("title", "item_name", "product_name", "produto") or
                    find("name", exclude=("model", "shop", "file")),
        # sale_price = preço com desconto (atual); price = preço cheio (original)
        "price":    find("sale_price", "item_price", "preco", "preço") or exact("price"),
        "original": find("original_price", "market_price", "list_price", "preco_original") or exact("price"),
        # prefere o image_link principal, senão qualquer imagem
        "image":    exact("image_link") or find("image", "imagem", "img"),
        # Link de AFILIADO = o "short link" (shope.ee). Nunca o product_link cru nem imagem.
        "url":      find("short link", "short_link", "offer_link", "affiliate", "shope.ee",
                         exclude=("image", "img")) or
                    find("product_link", "item_url", "product_url",
                         exclude=("image", "img", "short")),
        "category": find("global_category3", "global_category", "category", "categoria"),
        "discount": find("discount", "desconto"),
        "sales":    find("item_sales", "historical_sold", "sold", "sales", "vendas"),
    }


MAX_FEED_BYTES = 4 * 1024 * 1024  # lê no máx ~4MB do feed (evita timeout/memória na Vercel)


def _download_feed_text(url, max_bytes=MAX_FEED_BYTES):
    """Baixa o feed em streaming, parando após max_bytes (feeds Shopee são enormes)."""
    chunks, total = [], 0
    with requests.get(url, timeout=9, stream=True,
                      headers={"User-Agent": "Mozilla/5.0"}) as r:
        if r.status_code != 200:
            print(f"[SHOPEE] Feed retornou {r.status_code}")
            return None
        for chunk in r.iter_content(chunk_size=65536):
            if not chunk:
                continue
            chunks.append(chunk)
            total += len(chunk)
            if total >= max_bytes:
                break
    return b"".join(chunks).decode("utf-8-sig", errors="replace")


def _parse_feed(url):
    try:
        content = _download_feed_text(url)
        if not content:
            return []

        sample = content[:2000]
        delimiter = "\t" if sample.count("\t") > sample.count(",") else ","
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        rows = list(reader)
        # Descarta a última linha (pode estar cortada pelo limite de bytes)
        if len(rows) > 2:
            rows = rows[:-1]
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

            # Segurança: se "link" e "imagem" estiverem trocados, corrige
            img_exts = (".jpg", ".jpeg", ".png", ".webp", ".gif")
            if url_link.lower().endswith(img_exts) and not image.lower().endswith(img_exts):
                url_link, image = image, url_link
            # Se o link de compra ainda for uma imagem, descarta o produto
            if url_link.lower().endswith(img_exts):
                continue

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
