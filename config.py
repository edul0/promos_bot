import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "") # ID do grupo ou canal onde o bot vai postar

# Gemini IA (Opcional - mas recomendado para anúncios personalizados)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Shopee Affiliate
SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID", "")
SHOPEE_APP_SECRET = os.getenv("SHOPEE_APP_SECRET", "")

# Mercado Livre Affiliate
ML_APP_ID = os.getenv("ML_APP_ID", "")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET", "")
