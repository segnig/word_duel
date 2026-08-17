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


def _proxy_from_env():
    for key in (
        "TELEGRAM_PROXY",
        "HTTPS_PROXY",
        "https_proxy",
        "HTTP_PROXY",
        "http_proxy",
        "ALL_PROXY",
        "all_proxy",
    ):
        value = os.environ.get(key)
        if value:
            return value.strip()
    return None


TELEGRAM_PROXY = _proxy_from_env()
TELEGRAM_TIMEOUT = float(os.environ.get("TELEGRAM_TIMEOUT", 30))
