import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "") # ID do grupo ou canal onde o bot vai postar

# Gemini IA (Opcional - mas recomendado para anúncios personalizados)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Mercado Livre Afiliado (parâmetros de rastreamento de comissão)
ML_MATT_TOOL = os.getenv("ML_MATT_TOOL", "")
ML_MATT_WORD = os.getenv("ML_MATT_WORD", "")

# Mercado Livre OAuth (API autenticada - produtos reais com imagem)
ML_CLIENT_ID = os.getenv("ML_CLIENT_ID", "5392849814594048")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET", "")

# Shopee Affiliate (para quando quiser ativar)
SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID", "")
SHOPEE_APP_SECRET = os.getenv("SHOPEE_APP_SECRET", "")
