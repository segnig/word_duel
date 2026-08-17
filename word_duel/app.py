import logging

import httpx
from telegram.error import NetworkError, TimedOut
from telegram.ext import ApplicationBuilder
from telegram.request import HTTPXRequest

from word_duel.config import BOT_TOKEN, MONGO_URI, TELEGRAM_PROXY, TELEGRAM_TIMEOUT
from word_duel.db import check_connection
from word_duel.handlers import register_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


def _telegram_request():
    return HTTPXRequest(
        connect_timeout=TELEGRAM_TIMEOUT,
        read_timeout=TELEGRAM_TIMEOUT,
        write_timeout=TELEGRAM_TIMEOUT,
        pool_timeout=TELEGRAM_TIMEOUT,
        proxy=TELEGRAM_PROXY,
    )


def verify_telegram():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    kwargs = {"timeout": TELEGRAM_TIMEOUT}
    if TELEGRAM_PROXY:
        kwargs["proxy"] = TELEGRAM_PROXY
    response = httpx.get(url, **kwargs)
    response.raise_for_status()
    username = response.json()["result"]["username"]
    log.info("Telegram OK (@%s)", username)


def build_app():
    request = _telegram_request()
    builder = ApplicationBuilder().token(BOT_TOKEN).request(request).get_updates_request(request)
    app = builder.build()
    register_handlers(app)
    return app


def main():
    log.info("Word Duel bot starting...")
    if "YOUR_BOT_TOKEN" in BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("Set BOT_TOKEN in .env before running.")
    check_connection()
    log.info("MongoDB connected (%s)", "Atlas" if MONGO_URI.startswith("mongodb+srv") else "local")
    if TELEGRAM_PROXY:
        log.info("Using proxy for Telegram: %s", TELEGRAM_PROXY.split("@")[-1])
    try:
        verify_telegram()
    except httpx.ConnectError as exc:
        if TELEGRAM_PROXY and "127.0.0.1" in TELEGRAM_PROXY:
            raise RuntimeError(
                f"Proxy is set ({TELEGRAM_PROXY}) but nothing is listening.\n"
                "Start Clash/V2Ray first, or fix the port in .env, or remove TELEGRAM_PROXY.\n"
                "Easiest fix: deploy to Render — docs/DEPLOY.md"
            ) from exc
        raise RuntimeError(
            "Cannot reach Telegram. MongoDB is OK.\n"
            "Deploy to Render (docs/DEPLOY.md) or start a VPN/proxy."
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            "Cannot reach Telegram (api.telegram.org). MongoDB is OK.\n"
            "Deploy to Render (docs/DEPLOY.md), or start Clash/V2Ray on the port in TELEGRAM_PROXY."
        ) from exc
    try:
        build_app().run_polling(drop_pending_updates=True, bootstrap_retries=5)
    except (TimedOut, NetworkError) as exc:
        raise RuntimeError(
            "Lost connection to Telegram while running.\n"
            "Deploy to Render (docs/DEPLOY.md) so the bot stays online 24/7."
        ) from exc
