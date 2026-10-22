# Promos bot

Publicação de produtos de Mercado Livre/Shopee e leitor pessoal de ofertas/cupons.

## Publicação existente

`/api/cron` mantém o destino `TELEGRAM_CHAT_ID`. Agora exige Redis disponível,
usa uma trava para evitar disparos simultâneos e registra o histórico somente
depois da confirmação do Telegram. O mesmo título na mesma loja fica bloqueado
por sete dias, exceto quando o preço cai pelo menos 3%. Categorias da Shopee se
alternam quando há opções, incluindo variedades além de Pokémon e PC.

O catálogo com preços fixos foi desativado e preços anteriores não são estimados.
Preço da API/feed não significa que o produto seja uma promoção histórica.
Não há consulta automática ao checkout nem confirmação de frete/estoque.

Mercado Livre: só publica quando o gerador oficial da conta configurada retorna
um link. Configure `ML_AFFILIATE_COOKIE`, `ML_AFFILIATE_CSRF` e
`ML_AFFILIATE_TAG`. A sessão expira e pode precisar de renovação. Parâmetros
`matt_tool` sozinhos não são usados como garantia de atribuição de comissão.
Shopee: configure os feeds da **sua conta de afiliado** em `SHOPEE_FEED_URL_1/2`;
o bot usa o link de afiliado fornecido pelo feed, sem converter links de rivais.

## Leitor pessoal 24 horas

O leitor é um processo separado da API web e requer um servidor com processo
contínuo e disco persistente. Os dados não são enviados a modelos de IA.
Ele acompanha novas mensagens e edições de grupos/canais acessíveis à conta;
não varre o histórico, não entra em novos grupos e não monitora conversas privadas.

1. Instale Python 3.11+ e execute `python -m venv .venv`.
2. Ative o ambiente e execute `pip install -r requirements-watch.txt`.
3. Copie `.env.example` para `.env` e configure as credenciais. Obtenha seu
   `TELEGRAM_API_ID` e `TELEGRAM_API_HASH` em <https://my.telegram.org>.
4. Inicie conversa com seu bot. Configure seu ID privado em
   `TELEGRAM_ALERT_CHAT_ID`, separado do grupo público de promoções.
5. Faça login no terminal com `python telegram_watch.py --login`.
   Digite código e senha de duas etapas diretamente no terminal; não os envie no chat.
6. Opcional: `python telegram_watch.py --list-chats` lista IDs. Em
   `watchlist.json`, desative `watch_all_groups` e preencha `chat_ids` para
   selecionar apenas grupos de ofertas. Por padrão acompanha todos os grupos/canais.
7. Execute `python telegram_watch.py` e mantenha o processo ativo.

`watchlist.json` já inclui Switch 2 exclusivamente com domínio Mercado Livre e
cadeiras de escritório/ergonômicas, sem teto de preço. Ajuste `max_price` quando
definir seu orçamento. O filtro é textual; não identifica produtos apenas em
imagens. Com teto configurado usa o primeiro valor `R$` do texto, que pode ser
o preço anterior; não calcula preço líquido de cupom.

Avisos que mencionem cupom/cupons geram alerta privado com condições da mensagem
original. Não confirma validade, resgate ou elegibilidade para sua conta.
O mesmo texto, ignorando URLs, fica bloqueado por sete dias. Mensagens com texto
diferente podem gerar um novo alerta do mesmo cupom; edições com regras diferentes
também geram novo alerta. Não há alerta de expiração inferida.

Para produtos ML, tenta resolver links ML conhecidos e gerar seu link oficial.
Se não conseguir, retém o alerta de produto. Avisos de cupom podem chegar sem
link de compra. Links comerciais da origem são removidos do corpo do alerta;
a referência à mensagem original é mantida. Encurtadores externos e conversão
de links Shopee de terceiros ainda não são suportados. O leitor envia **somente
ao seu privado**; não republica automaticamente posts rivais no seu canal.

Para Linux, há exemplo em `deploy/promos-watch.service`. Instale o projeto em
`/opt/promos_bot`, crie o usuário de serviço `promos`, instale as dependências
no `.venv` desse diretório e configure `WATCH_DATA_DIR=/var/lib/promos-watch`.
Faça o login como usuário `promos` usando esse diretório de dados antes de
habilitar o serviço. Copie o arquivo para `/etc/systemd/system/`, execute
`systemctl daemon-reload` e `systemctl enable --now promos-watch`.
Consulte `journalctl -u promos-watch` para diagnóstico.

Guarde `.env` e o diretório de dados em local privado. O arquivo `.session`
autoriza acesso à conta. Não publique esses arquivos no GitHub.

Limitações: monitora enquanto conectado; não recupera automaticamente mensagens
perdidas durante uma parada. Falhas no envio são registradas no log. Redis e
Telegram não formam uma transação: queda após enviar e antes de salvar pode
causar repetição. Execute apenas uma instância do leitor por sessão.

## Entrada de cupons pelo bot existente

Encaminhe um aviso de cupom ML ao grupo configurado ou ao privado do bot
(neste caso, o remetente deve ser administrador do grupo configurado).
`/api/coupons/sync` importa os avisos e publica os novos cupons no grupo.
O `/api/cron` também executa essa importação antes de selecionar uma oferta.
Este fluxo usa getUpdates e não remove webhooks existentes; se houver webhook,
a integração precisa ser feita nele. Depende de o bot receber a mensagem
(mensagens comuns do grupo podem estar limitadas pelo privacy mode).

O aviso deve conter Mercado Livre, código explícito (ex.: `Cupom: CODIGO10`),
desconto e condições. Para anexar a produtos automaticamente exige validade
informada, mínimo de compra e escopo identificável; percentuais exigem teto.
Restrições de conta, pagamento, Full e produtos selecionados ficam como avisos,
sem anexação automática. A estimativa anexada sempre depende da elegibilidade
no carrinho. Não há descoberta automática no site oficial nem leitor de grupos
ativo até a configuração separada do processo contínuo.

Cupons sem validade explícita ficam como aviso durante 24h. Não é confirmação
de vigência. Avisos incompatíveis são contados no diagnóstico, sem expor o texto recebido. Não use o endpoint como API pública de divulgação.

## Testes

`python -m unittest discover -s tests -v`

Os testes usam mensagens e respostas simuladas, sem postar no Telegram ou
acessar as contas. A validação ao vivo depende das credenciais e do servidor.
