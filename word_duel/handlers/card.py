from telegram.error import BadRequest

from word_duel.card import render_card
from word_duel.keyboards import game_keyboard


def game_id_from_query(query):
    if query.inline_message_id:
        return f"inline:{query.inline_message_id}"
    if query.message:
        return query.message.chat.id
    return None


async def refresh_card(game, query=None, bot=None):
    text = render_card(game)
    markup = game_keyboard(game)
    try:
        if query is not None:
            await query.edit_message_text(text=text, reply_markup=markup)
            return True
        if not bot:
            return False
        if game.get("inline_message_id"):
            await bot.edit_message_text(
                text=text,
                inline_message_id=game["inline_message_id"],
                reply_markup=markup,
            )
            return True
        if game.get("message_id") is not None and game.get("host_chat_id") is not None:
            await bot.edit_message_text(
                text=text,
                chat_id=game["host_chat_id"],
                message_id=game["message_id"],
                reply_markup=markup,
            )
            return True
    except BadRequest as exc:
        if "not modified" in str(exc).lower():
            return True
        raise
    return False
