import requests

# Testa diferentes formatos de URL de imagem do ML
urls = [
    "https://http2.mlstatic.com/D_NQ_NP_895398-MLA45642874100_042021-O.jpg",
    "https://http2.mlstatic.com/D_NQ_NP_2X_895398-MLA45642874100_042021-F.jpg",
    "https://http2.mlstatic.com/D_NQ_NP_895398-MLA45642874100_042021-F.webp",
]

for u in urls:
    r = requests.get(u, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
    print(f"URL: ...{u[-30:]}")
    print(f"  Status: {r.status_code}, Size: {len(r.content)}, Type: {r.headers.get('content-type','?')}")
    print()

# Testa se a API do ML funciona com IP diferente
print("=== Testando endpoints alternativos do ML ===")
endpoints = [
    "https://api.mercadolibre.com/sites/MLB/search?q=celular&limit=2",
    "https://api.mercadolibre.com/highlights/MLB/deal_of_the_day",
    "https://api.mercadolibre.com/trends/MLB",
]
for ep in endpoints:
    r = requests.get(ep, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=5)
    print(f"Endpoint: {ep.split('/')[-1][:50]}")
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, list):
            print(f"  Resultados: {len(data)}")
            if data:
                print(f"  Primeiro: {data[0]}")
        elif isinstance(data, dict):
            results = data.get("results", [])
            print(f"  Resultados: {len(results)}")
            if results:
                p = results[0]
                thumb = p.get("thumbnail", "N/A")
                print(f"  Titulo: {p.get('title','?')}")
                print(f"  Thumbnail: {thumb}")
                if thumb and thumb != "N/A":
                    big = thumb.replace("-I.jpg", "-O.jpg")
                    ri = requests.get(big, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                    print(f"  Imagem Grande: Status={ri.status_code}, Size={len(ri.content)}, Type={ri.headers.get('content-type','?')}")
    print()
