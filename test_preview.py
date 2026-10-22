"""Simulação pública dos filtros: não envia mensagens nem gera links comerciais."""
import json
from pathlib import Path
from flask import Blueprint, jsonify, request
from telegram_watch import match_labels

preview = Blueprint('test_preview', __name__)
CONFIG = json.loads(Path(__file__).with_name('watchlist.json').read_text(encoding='utf-8'))


@preview.get('/teste')
def page():
    return '''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Teste dos alertas · Promos Bot</title>
<style>body{font:17px system-ui;background:#101820;color:#edf5f5;max-width:780px;margin:48px auto;padding:20px}h1{font-size:32px}textarea{box-sizing:border-box;width:100%;min-height:230px;background:#1b2935;color:white;border:1px solid #698089;border-radius:12px;padding:16px;font:16px system-ui}button{background:#9be6c3;border:0;border-radius:8px;padding:13px 20px;font:inherit;cursor:pointer;margin:12px 6px 12px 0}p{line-height:1.6}#result{border:1px solid #698089;border-radius:12px;padding:20px;white-space:pre-wrap}small{color:#c5d2da}</style>
<h1>Teste seus alertas de ofertas</h1>
<p>Cole uma mensagem para ver se ela aciona seus filtros. Esta simulação não envia nada ao Telegram, não acessa seus grupos e não gera links de afiliado.</p>
<label for="message">Mensagem da oferta ou cupom</label>
<textarea id="message" maxlength="12000">Nintendo Switch 2 por R$ 3.400,00
https://www.mercadolivre.com.br/p/MLB123
Cupom EXEMPLO: 10% OFF, limitado a R$ 200. Resgate no app.
(Mensagem fictícia para testar os filtros.)</textarea>
<button id="test">Testar mensagem</button><button id="chair">Exemplo de cadeira</button>
<div id="result" role="status" aria-live="polite">O resultado aparecerá aqui.</div>
<p><small>Foco atual: Switch 2 no Mercado Livre, cadeiras ergonômicas/de escritório e mensagens com cupom. Sem teto de preço configurado. Um alerta textual não confirma validade do cupom, estoque, preço final nem comissão. Links de compra reais precisam passar pelo gerador da sua conta.</small></p>
<script>
document.getElementById('chair').onclick=()=>{document.getElementById('message').value='Cadeira ergonômica de escritório com ajuste lombar por R$ 899,00';};
document.getElementById('test').onclick=async()=>{
const result=document.getElementById('result');result.textContent='Testando…';
try{const response=await fetch('/api/test_match',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:document.getElementById('message').value})});
const data=await response.json();if(!response.ok)throw new Error(data.error||'Falha no teste');
result.textContent=data.labels.length?'Alertas que seriam acionados:\\n\\n'+data.labels.join('\\n\\n'):'Nenhum filtro acionado. Confira o modelo, a loja e as palavras da mensagem.';
}catch(error){result.textContent=error.message;}};
</script></html>'''


@preview.post('/api/test_match')
def test_match():
    if request.content_length and request.content_length > 50000:
        return jsonify(error='Mensagem muito grande.'), 413
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('text'), str):
        return jsonify(error='Informe text como texto.'), 400
    text = data['text']
    if len(text) > 12000:
        return jsonify(error='Use até 12.000 caracteres.'), 400
    return jsonify(labels=match_labels(text, CONFIG), simulation=True,
                   affiliate_link_generated=False, sent_to_telegram=False)
