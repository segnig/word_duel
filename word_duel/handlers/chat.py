from telegram import Update
from telegram.ext import ContextTypes

from word_duel import db, duel, texts
from word_duel.constants import STATUS_IN_PROGRESS, STATUS_SETUP
from word_duel.game_logic import is_valid_word, normalize_word
from word_duel.handlers.common import (
    announce_secret_result,
    reply_guess_result,
    try_hide_message,
)


async def handle_group_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Let both players set words and guess in the group chat, not only via DMs."""
    message = update.message
    if not message or not message.text:
        return

    game = db.get_game(update.effective_chat.id)
    if not game:
        return

    user = update.effective_user
    role = duel.role_for_user(game, user.id)
    if not role:
        return

    word = normalize_word(message.text)
    if not is_valid_word(word, game["word_length"]):
        return

    if game["status"] == STATUS_SETUP:
        if game["players"][role].get("secret_word"):
            return
        hidden = await try_hide_message(message)
        try:
            result = duel.submit_secret_word(user.id, word)
        except duel.DuelError as exc:
            await update.effective_chat.send_message(exc.message)
            return
        if result is None:
            return
        if not hidden:
            await update.effective_chat.send_message(texts.could_not_hide_word())
        await announce_secret_result(update, context, result)
        return

    if game["status"] != STATUS_IN_PROGRESS:
        return
    if user.id != game["players"][game["turn"]]["user_id"]:
        return

    try:
        result = duel.make_guess(game, user, word)
    except duel.DuelError as exc:
        await message.reply_text(exc.message)
        return
    await reply_guess_result(message, result)
