from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ContextTypes

from word_duel import db, duel
from word_duel.card import render_card
from word_duel.constants import ROLE_A
from word_duel.game_logic import normalize_word
from word_duel.inline_query import parse_inline_query
from word_duel.keyboards import game_keyboard


def _join_callback(host_id, length, host_word=None):
    data = f"join:{host_id}:{length}"
    if host_word:
        data = f"{data}:{host_word}"
    return data


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    length, host_word, error = parse_inline_query(query.query)

    if error:
        await query.answer(
            [
                InlineQueryResultArticle(
                    id="error",
                    title="Invalid game",
                    description=error,
                    input_message_content=InputTextMessageContent(f"❌ {error}"),
                )
            ],
            cache_time=0,
            is_personal=True,
        )
        return

    if host_word:
        title = f"Word Duel · {host_word} ({length} letters)"
        description = "Your word is set. Friend joins and tries to guess yours."
        preview = f"🎮 Word Duel · {length} letters\n\nHost word is set. Tap Join to play."
    else:
        title = f"Word Duel ({length} letters)"
        description = "Or type CRANE / 6 MONKEY to set your secret word now."
        preview = f"🎮 Word Duel · {length} letters\n\nWaiting to start…"

    await query.answer(
        [
            InlineQueryResultArticle(
                id=f"duel-{length}-{host_word or ''}",
                title=title,
                description=description,
                input_message_content=InputTextMessageContent(preview),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "Join game",
                        callback_data=_join_callback(query.from_user.id, length, host_word),
                    )]
                ]),
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

    length, host_word, _ = parse_inline_query(chosen.query)

    game_id = f"inline:{inline_id}"
    game = db.get_game(game_id)
    if not game:
        game = duel.start_game(game_id, chosen.from_user, length, host_word=host_word)
    else:
        role = duel.role_for_user(game, chosen.from_user.id)
        if role:
            game["players"][role]["name"] = chosen.from_user.first_name
        if host_word and not game["players"][ROLE_A].get("secret_word"):
            word = normalize_word(host_word)
            if len(word) == game["word_length"]:
                game["players"][ROLE_A]["secret_word"] = word
    game["inline_message_id"] = inline_id
    db.save_game(game)

    await context.bot.edit_message_text(
        text=render_card(game),
        inline_message_id=inline_id,
        reply_markup=game_keyboard(game),
    )
