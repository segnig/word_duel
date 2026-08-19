"""
Configuration for Word Duel. All values can be overridden with
environment variables so secrets never need to be hardcoded.

Copy .env.example to .env and fill in your Atlas connection string.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Local: mongodb://localhost:27017
# Atlas: mongodb+srv://USER:PASSWORD@cluster....mongodb.net/?retryWrites=true&w=majority
MONGO_URI = (
    os.environ.get("MONGO_URI")
    or os.environ.get("MONGODB_URI")
    or "mongodb://localhost:27017"
).strip()
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "word_duel")

DEFAULT_WORD_LENGTH = int(os.environ.get("WORD_LENGTH", 5))
DEFAULT_MAX_ROUNDS = int(os.environ.get("MAX_ROUNDS", 10))
GAME_TIMEOUT_MINUTES = int(os.environ.get("GAME_TIMEOUT_MINUTES", 10))

# Local proxy only — do not inherit HTTPS_PROXY (hosts like Render inject that).
TELEGRAM_PROXY = (os.environ.get("TELEGRAM_PROXY") or "").strip() or None
TELEGRAM_TIMEOUT = float(os.environ.get("TELEGRAM_TIMEOUT", 30))

PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = (
    os.environ.get("WEBHOOK_URL") or os.environ.get("RENDER_EXTERNAL_URL") or ""
).rstrip("/")
WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH", "/telegram")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET") or ""
HEALTH_PATH = os.environ.get("HEALTH_PATH", "/health")
