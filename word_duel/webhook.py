"""Starlette app: Telegram webhook + /health for Render."""

import logging
from contextlib import asynccontextmanager
from http import HTTPStatus

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.routing import Route
from telegram import Update
from telegram.ext import Application

from word_duel.config import HEALTH_PATH, WEBHOOK_PATH, WEBHOOK_SECRET, WEBHOOK_URL
from word_duel.health import health_payload

log = logging.getLogger(__name__)


def webhook_url():
    path = WEBHOOK_PATH if WEBHOOK_PATH.startswith("/") else f"/{WEBHOOK_PATH}"
    return f"{WEBHOOK_URL}{path}"


def build_webhook_app(application: Application) -> Starlette:
    path = WEBHOOK_PATH if WEBHOOK_PATH.startswith("/") else f"/{WEBHOOK_PATH}"
    health_path = HEALTH_PATH if HEALTH_PATH.startswith("/") else f"/{HEALTH_PATH}"

    async def telegram(request: Request) -> Response:
        if WEBHOOK_SECRET:
            token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if token != WEBHOOK_SECRET:
                return Response(status_code=HTTPStatus.FORBIDDEN)
        try:
            data = await request.json()
            update = Update.de_json(data=data, bot=application.bot)
            if update:
                await application.update_queue.put(update)
        except Exception:
            log.exception("Failed to handle Telegram webhook update")
        return Response(status_code=HTTPStatus.OK)

    async def health(_: Request) -> JSONResponse:
        status, body = health_payload()
        code = HTTPStatus.OK if status == "ok" else HTTPStatus.SERVICE_UNAVAILABLE
        return JSONResponse(body, status_code=code)

    async def root(_: Request) -> PlainTextResponse:
        return PlainTextResponse("word-duel")

    @asynccontextmanager
    async def lifespan(_app: Starlette):
        async with application:
            url = webhook_url()
            await application.bot.set_webhook(
                url=url,
                secret_token=WEBHOOK_SECRET or None,
                drop_pending_updates=False,
                allowed_updates=Update.ALL_TYPES,
            )
            info = await application.bot.get_webhook_info()
            log.info("Telegram webhook set to %s (pending=%s)", info.url, info.pending_update_count)
            await application.start()
            yield
            await application.stop()
            # Keep the webhook registered. Deleting it on Render sleep/restart
            # makes Telegram drop updates and the bot goes silent.

    return Starlette(
        routes=[
            Route(path, telegram, methods=["POST"]),
            Route(health_path, health, methods=["GET"]),
            Route("/healthz", health, methods=["GET"]),
            Route("/", root, methods=["GET"]),
        ],
        lifespan=lifespan,
    )
