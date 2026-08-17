"""
Configuration for Word Duel. All values can be overridden with
environment variables so secrets never need to be hardcoded.
"""
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "word_duel")

DEFAULT_WORD_LENGTH = int(os.environ.get("WORD_LENGTH", 5))
DEFAULT_MAX_ROUNDS = int(os.environ.get("MAX_ROUNDS", 10))
