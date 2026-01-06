
import os
from dotenv import load_dotenv
import re

load_dotenv()

# --- Основные настройки ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 1337))

# --- Настройки базы данных ---
DB_PATH = "database/database.db"

# --- Настройки YooMoney ---
YOOMONEY_ACCESS_TOKEN = os.getenv("YOOMONEY_ACCESS_TOKEN")
YOOMONEY_CLIENT_ID = os.getenv("YOOMONEY_CLIENT_ID")
YOOMONEY_REDIRECT_URI = os.getenv("YOOMONEY_REDIRECT_URI")
YOOMONEY_CHECK_INTERVAL = 45  # секунд (для поллинга)
YOOMONEY_DRY_RUN = os.getenv("YOOMONEY_DRY_RUN", "False").lower() == "true"
YOOMONEY_WEBHOOK_ENABLED = False # Отключаем вебхуки, только поллинг
YOOMONEY_NOTIFICATION_SECRET = os.getenv("YOOMONEY_NOTIFICATION_SECRET")
YOOMONEY_WEBHOOK_HOST = "0.0.0.0"
YOOMONEY_WEBHOOK_PORT = 8080
YOOMONEY_WEBHOOK_PATH = "/webhook/yoomoney"

# --- Настройки OhMyGPT ---
OHMYGPT_API_KEY = os.getenv("OHMYGPT_API_KEY")
OHMYGPT_API_URL = "https://ohmygpt.com/api/v1/chat/completions" # Проверьте URL
OHMYGPT_MODEL = "gpt-4o-mini"
OHMYGPT_FALLBACK_MODELS = ["gpt-3.5-turbo", "gpt-4o"]

# --- Настройки логики ---
INITIAL_FREE_REQUESTS = 3
INITIAL_PREMIUM_REQUESTS = 1
FREE_REQUEST_INTERVAL = 8 * 3600  # 8 часов
MAX_CARDS = 7
MAX_QUESTION_LENGTH = 300
BAN_DURATION_HOURS = 24
MAX_FORBIDDEN_ATTEMPTS = 3
TIMEZONE = "Europe/Moscow"
TAROT_READER_NAME = "Луна"
BOT_USERNAME = "@TaroLunaBot" # Замените на реальный юзернейм

# --- Фильтр запрещенных слов ---
FORBIDDEN_KEYWORDS = re.compile(
    r"(смерт|умереть|убил|суицид|наркотик|теракт|бомба|оружие|насилие|изнасилов|детск.*порно)",
    re.IGNORECASE
)

# --- Настройки логов ---
LOG_PATH = "logs/bot.log"
YOOMONEY_LOG_PATH = "logs/yoomoney.log"

# --- Тарифы ---
PAYMENT_OPTIONS = {
    "buy_1": {"requests": 1, "price": 99, "label": "🔮 1 расклад - 99₽"},
    "buy_3": {"requests": 3, "price": 249, "label": "✨ 3 расклада - 249₽ (Выгодно!)"},
    "buy_5": {"requests": 5, "price": 399, "label": "🌟 5 раскладов - 399₽ (Хит!)"},
    "buy_10": {"requests": 10, "price": 699, "label": "💎 10 раскладов - 699₽ (VIP)"},
}