from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ContextTypes

from word_duel.config import DEFAULT_WORD_LENGTH
from word_duel.constants import MAX_WORD_LENGTH, MIN_WORD_LENGTH
from word_duel import duel
from word_duel.card import render_card
from word_duel.keyboards import game_keyboard, join_keyboard


def _length_from_query(text):
    raw = (text or "").strip()
    if raw.isdigit():
        value = int(raw)
        if MIN_WORD_LENGTH <= value <= MAX_WORD_LENGTH:
            return value
    return DEFAULT_WORD_LENGTH


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    length = _length_from_query(query.query)
    title = f"Word Duel ({length} letters)"
    await query.answer(
        [
            InlineQueryResultArticle(
                id=f"duel-{length}",
                title=title,
                description="Send a game to this chat. Opponent taps Join, then play on the buttons.",
                input_message_content=InputTextMessageContent(
                    f"🎮 Word Duel · {length} letters\n\nWaiting to start…"
                ),
                reply_markup=join_keyboard(),
            )
        ],
        cache_time=0,
        is_personal=True,
    )


async def chosen_inline_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chosen = update.chosen_inline_result
    inline_id = chosen.inline_message_id
    if not inline_id:
        return

    length = DEFAULT_WORD_LENGTH
    if chosen.result_id.startswith("duel-"):
        try:
            length = int(chosen.result_id.split("-", 1)[1])
        except ValueError:
            pass

    game_id = f"inline:{inline_id}"
    game = duel.start_game(game_id, chosen.from_user, length)
    game["inline_message_id"] = inline_id
    from word_duel import db
    db.save_game(game)

    await context.bot.edit_message_text(
        text=render_card(game),
        inline_message_id=inline_id,
        reply_markup=game_keyboard(game),
    )
