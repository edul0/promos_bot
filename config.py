import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "") # ID do grupo ou canal onde o bot vai postar

# Gemini IA (Opcional - mas recomendado para anúncios personalizados)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Mercado Livre Afiliado (Método Simples - só o ID, sem cookie!)
ML_MATT_TOOL = os.getenv("ML_MATT_TOOL", "82883927")
ML_MATT_WORD = os.getenv("ML_MATT_WORD", "matoscarlos20220825095337")

# Shopee Affiliate (para quando quiser ativar)
SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID", "")
SHOPEE_APP_SECRET = os.getenv("SHOPEE_APP_SECRET", "")
