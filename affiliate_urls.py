"""Conversão ML com o gerador da conta configurada; nunca reutiliza tag rival."""
import re
from urllib.parse import urlsplit, urlunsplit
import requests
from ml_affiliate import generate_official_affiliate_link


def is_ml_host(host):
    return host in ('meli.la', 'mercadolivre.com', 'mercadolivre.com.br') or host.endswith('.mercadolivre.com.br')


def own_ml_link(url):
    # Resolve só redirecionamentos ML conhecidos, sem seguir hosts arbitrários.
    current = url
    try:
        for _ in range(6):
            parsed = urlsplit(current)
            if parsed.scheme != 'https' or not is_ml_host(parsed.hostname or '') or parsed.username or parsed.password:
                return None
            if re.search(r'(?:/p/MLB\d+|MLB-?\d+)', parsed.path, re.I):
                clean = urlunsplit(('https', parsed.netloc, parsed.path, '', ''))
                return generate_official_affiliate_link(clean)
            response = requests.get(current, allow_redirects=False, timeout=8,
                                    headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
            try:
                if response.is_redirect:
                    from urllib.parse import urljoin
                    current = urljoin(current, response.headers['Location'])
                else:
                    return None
            finally:
                response.close()
    except requests.RequestException:
        return None
    return None
