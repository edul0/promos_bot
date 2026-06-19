"""
Geração do link de afiliado OFICIAL do Mercado Livre (formato meli.la/social),
replicando a chamada interna do "Gerador de Links" do painel de afiliados:

    POST /affiliate-program/api/v2/affiliates/createLink
    headers: x-csrf-token + cookie (sessão logada do afiliado)
    body: {"urls": ["<url do produto>"], "tag": "<etiqueta>"}

IMPORTANTE: isso usa a SESSÃO do navegador do afiliado (cookies), que EXPIRA.
Quando expira, retorna None e o chamador usa o link /p/...matt_tool como fallback.

Configurar na Vercel:
    ML_AFFILIATE_COOKIE  -> a string de cookie da sua sessão do mercadolivre.com.br
    ML_AFFILIATE_CSRF    -> o valor do header x-csrf-token
    ML_AFFILIATE_TAG     -> sua etiqueta (ex: matoscarlos20220825095337)
"""
import os
import re
import requests

CREATE_LINK_URL = "https://www.mercadolivre.com.br/affiliate-program/api/v2/affiliates/createLink"

ML_AFFILIATE_COOKIE = os.getenv("ML_AFFILIATE_COOKIE", "")
ML_AFFILIATE_CSRF = os.getenv("ML_AFFILIATE_CSRF", "")
ML_AFFILIATE_TAG = os.getenv("ML_AFFILIATE_TAG") or os.getenv("ML_MATT_WORD", "")

_MELI_LA_RE = re.compile(r"https://meli\.la/[A-Za-z0-9]+")


def generate_official_affiliate_link(product_url):
    """
    Tenta gerar o link curto oficial (meli.la). Retorna a URL ou None se falhar
    (sessão ausente/expirada, produto não permitido, etc.).
    """
    if not (ML_AFFILIATE_COOKIE and ML_AFFILIATE_CSRF and ML_AFFILIATE_TAG):
        return None

    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://www.mercadolivre.com.br",
        "referer": "https://www.mercadolivre.com.br/afiliados/linkbuilder",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "x-csrf-token": ML_AFFILIATE_CSRF,
        "cookie": ML_AFFILIATE_COOKIE,
    }
    payload = {"urls": [product_url], "tag": ML_AFFILIATE_TAG}

    try:
        r = requests.post(CREATE_LINK_URL, headers=headers, json=payload, timeout=12)
        if r.status_code != 200:
            print(f"createLink status {r.status_code}: {r.text[:200]}")
            return None
        # O corpo varia; procuramos o link meli.la em qualquer formato de resposta.
        m = _MELI_LA_RE.search(r.text)
        if m:
            return m.group(0)
        print(f"createLink sem meli.la na resposta: {r.text[:200]}")
    except Exception as e:
        print(f"Erro createLink: {e}")
    return None
