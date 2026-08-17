import logging

from telegram.ext import ApplicationBuilder

from word_duel.config import BOT_TOKEN
from word_duel.handlers import register_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    register_handlers(app)
    return app


def main():
    log.info("Word Duel bot starting...")
    build_app().run_polling()
