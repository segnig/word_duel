import logging

import httpx
from telegram.error import NetworkError, TimedOut
from telegram.ext import ApplicationBuilder
from telegram.request import HTTPXRequest

from word_duel.config import (
    BOT_TOKEN,
    MONGO_URI,
    PORT,
    TELEGRAM_PROXY,
    TELEGRAM_TIMEOUT,
    WEBHOOK_URL,
)
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


def build_app(*, webhook: bool = False):
    request = _telegram_request()
    builder = ApplicationBuilder().token(BOT_TOKEN).request(request)
    if webhook:
        builder = builder.updater(None)
    else:
        builder = builder.get_updates_request(request)
    app = builder.build()
    register_handlers(app)
    return app


def _ensure_ready():
    log.info("Word Duel bot starting...")
    if "YOUR_BOT_TOKEN" in BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("Set BOT_TOKEN in .env (or Render env) before running.")
    check_connection()
    log.info("MongoDB connected (%s)", "Atlas" if MONGO_URI.startswith("mongodb+srv") else "local")
    if TELEGRAM_PROXY:
        log.info("Using Telegram proxy: %s", TELEGRAM_PROXY.split("@")[-1])
    try:
        verify_telegram()
    except httpx.ConnectError as exc:
        if TELEGRAM_PROXY and "127.0.0.1" in TELEGRAM_PROXY:
            raise RuntimeError(
                f"Proxy is set ({TELEGRAM_PROXY}) but nothing is listening.\n"
                "Start Clash/V2Ray, or remove TELEGRAM_PROXY for Render."
            ) from exc
        raise RuntimeError(
            "Cannot reach Telegram. On Render this should work; locally use a VPN/proxy "
            "or deploy (docs/DEPLOY.md)."
        ) from exc


def run_webhook():
    try:
        import uvicorn
        from word_duel.webhook import build_webhook_app, webhook_url
    except ImportError as exc:
        raise RuntimeError(
            "Webhook extras missing. Run: pip install -r requirements.txt"
        ) from exc
    application = build_app(webhook=True)
    starlette_app = build_webhook_app(application)
    log.info("Webhook mode on port %s → %s", PORT, webhook_url())
    uvicorn.run(starlette_app, host="0.0.0.0", port=PORT, log_level="info")


def run_polling():
    log.info("Polling mode (no WEBHOOK_URL / RENDER_EXTERNAL_URL)")
    try:
        build_app(webhook=False).run_polling(drop_pending_updates=True, bootstrap_retries=5)
    except (TimedOut, NetworkError) as exc:
        raise RuntimeError(
            "Lost connection to Telegram while polling. Deploy to Render with webhooks."
        ) from exc


def main():
    _ensure_ready()
    if WEBHOOK_URL:
        run_webhook()
    else:
        run_polling()
