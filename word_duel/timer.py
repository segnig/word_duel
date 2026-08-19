"""Per-game countdown (default 10 minutes) and expiry."""

import asyncio
import logging
from datetime import timedelta, timezone

from word_duel import db
from word_duel.config import GAME_TIMEOUT_MINUTES
from word_duel.constants import (
    END_REASON_TIMEOUT,
    ROLE_A,
    ROLE_B,
    STATUS_FINISHED,
    STATUS_IN_PROGRESS,
    STATUS_SETUP,
)

log = logging.getLogger(__name__)

TIMER_REFRESH_SECONDS = 30


def new_expires_at():
    return db.now() + timedelta(minutes=GAME_TIMEOUT_MINUTES)


def reset_timer(game):
    game["expires_at"] = new_expires_at()


def _as_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def seconds_remaining(game):
    expires = _as_utc(game.get("expires_at"))
    if expires is None:
        return None
    return max(0, int((expires - db.now()).total_seconds()))


def format_countdown(seconds):
    minutes, secs = divmod(max(0, seconds), 60)
    return f"{minutes}:{secs:02d}"


def is_expired(game):
    remaining = seconds_remaining(game)
    return remaining is not None and remaining <= 0


def ensure_timer(game):
    if not game.get("expires_at"):
        reset_timer(game)
        db.save_game(game)


def expire_game(game):
    if not game or game.get("status") == STATUS_FINISHED:
        return False
    from word_duel.duel import is_solo

    game["status"] = STATUS_FINISHED
    game["end_reason"] = END_REASON_TIMEOUT
    if is_solo(game):
        game["winner"] = ROLE_B
    else:
        game["winner"] = "draw"
    db.save_game(game)
    return True


def apply_timeout_if_needed(game):
    if not game or game.get("status") == STATUS_FINISHED:
        return False
    ensure_timer(game)
    if not is_expired(game):
        return False
    return expire_game(game)


async def refresh_timers(bot):
    """Expire finished games and refresh cards so the countdown stays live."""
    from word_duel.handlers.card import refresh_card

    for game in db.list_active_games():
        try:
            ensure_timer(game)
            expired = apply_timeout_if_needed(game)
            if expired or game.get("status") in (STATUS_SETUP, STATUS_IN_PROGRESS):
                await refresh_card(game, bot=bot)
        except Exception:
            log.exception("Timer refresh failed for game %s", game.get("_id"))


async def run_timer_loop(application):
    while True:
        try:
            await asyncio.sleep(TIMER_REFRESH_SECONDS)
            await refresh_timers(application.bot)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Timer loop error")
