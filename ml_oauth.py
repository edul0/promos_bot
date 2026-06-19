"""
OAuth do Mercado Livre + armazenamento de tokens no Vercel KV (Upstash Redis).

Fluxo:
1. Usuário acessa /api/ml_auth -> redireciona para o ML autorizar
2. ML chama /api/ml_callback?code=... -> troca o code por tokens e salva no KV
3. get_valid_access_token() lê do KV e renova automaticamente quando expira

O refresh_token do ML é de uso único (rotaciona a cada renovação), por isso
precisamos persistir o novo token a cada refresh — o Vercel KV resolve isso.
"""
import os
import json
import time
from urllib.parse import urlencode

import requests

ML_CLIENT_ID = os.getenv("ML_CLIENT_ID", "5392849814594048")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET", "")

# Vercel KV (Upstash Redis) - injetado automaticamente ao criar o KV na Vercel
KV_URL = os.getenv("KV_REST_API_URL", "")
KV_TOKEN = os.getenv("KV_REST_API_TOKEN", "")
TOKEN_KEY = "ml_tokens"

AUTH_BASE = "https://auth.mercadolivre.com.br/authorization"
TOKEN_URL = "https://api.mercadolibre.com/oauth/token"


def _kv_headers():
    return {"Authorization": f"Bearer {KV_TOKEN}"}


def kv_get(key):
    if not KV_URL or not KV_TOKEN:
        return None
    try:
        r = requests.get(f"{KV_URL}/get/{key}", headers=_kv_headers(), timeout=8)
        if r.status_code == 200:
            return r.json().get("result")
    except Exception as e:
        print(f"KV get erro: {e}")
    return None


def kv_set(key, value):
    if not KV_URL or not KV_TOKEN:
        print("KV não configurado (KV_REST_API_URL / KV_REST_API_TOKEN ausentes)")
        return False
    try:
        # Upstash REST: POST /set/{key} com o valor no corpo da requisição
        r = requests.post(
            f"{KV_URL}/set/{key}",
            headers=_kv_headers(),
            data=value.encode("utf-8"),
            timeout=8,
        )
        return r.status_code == 200
    except Exception as e:
        print(f"KV set erro: {e}")
        return False


def save_tokens(token_data):
    record = {
        "access_token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
        # margem de 2 min antes do vencimento real (expires_in costuma ser 21600 = 6h)
        "expires_at": int(time.time()) + token_data.get("expires_in", 21600) - 120,
    }
    kv_set(TOKEN_KEY, json.dumps(record))
    return record


def load_tokens():
    raw = kv_get(TOKEN_KEY)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def get_authorization_url(redirect_uri):
    params = urlencode({
        "response_type": "code",
        "client_id": ML_CLIENT_ID,
        "redirect_uri": redirect_uri,
    })
    return f"{AUTH_BASE}?{params}"


def exchange_code(code, redirect_uri):
    """Troca o authorization code pelos tokens (chamado no callback)."""
    data = {
        "grant_type": "authorization_code",
        "client_id": ML_CLIENT_ID,
        "client_secret": ML_CLIENT_SECRET,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    r = requests.post(TOKEN_URL, data=data, timeout=10)
    r.raise_for_status()
    return save_tokens(r.json())


def refresh_tokens(refresh_token):
    """Renova o access_token usando o refresh_token (que também é rotacionado)."""
    data = {
        "grant_type": "refresh_token",
        "client_id": ML_CLIENT_ID,
        "client_secret": ML_CLIENT_SECRET,
        "refresh_token": refresh_token,
    }
    r = requests.post(TOKEN_URL, data=data, timeout=10)
    r.raise_for_status()
    return save_tokens(r.json())


def get_valid_access_token():
    """
    Retorna um access_token válido (renovando se necessário).
    Retorna None se ainda não houve autorização ou se algo falhou.
    """
    if not ML_CLIENT_SECRET:
        print("ML_CLIENT_SECRET não configurado")
        return None

    tokens = load_tokens()
    if not tokens:
        print("Nenhum token salvo. Autorize o app acessando /api/ml_auth")
        return None

    if int(time.time()) >= tokens.get("expires_at", 0):
        try:
            tokens = refresh_tokens(tokens["refresh_token"])
            print("Token do ML renovado com sucesso")
        except Exception as e:
            print(f"Erro ao renovar token do ML: {e}")
            return None

    return tokens.get("access_token")
