"""Tiny HTML helpers for Telegram parse_mode=HTML."""

from html import escape as _escape

PARSE_MODE = "HTML"


def esc(value):
    return _escape(str(value or ""), quote=False)


def bold(value):
    return f"<b>{esc(value)}</b>"


def italic(value):
    return f"<i>{esc(value)}</i>"


def spoiler(value):
    return f"<tg-spoiler>{esc(value)}</tg-spoiler>"


def code(value):
    return f"<code>{esc(value)}</code>"
