from telegram.ext import ContextTypes

from word_duel import db, duel
from word_duel.constants import STATUS_IN_PROGRESS
from word_duel.handlers.card import refresh_card
from word_duel.handlers.common import announce_secret_result, reply_guess_result


async def handle_private_message(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    game = db.get_game(chat_id)

    if game and duel.is_solo(game) and game["status"] == STATUS_IN_PROGRESS:
        try:
            guess = duel.make_guess(game, user, update.message.text)
        except duel.DuelError as exc:
            await update.message.reply_text(exc.message)
            return
        refreshed = await refresh_card(guess.game, bot=context.bot)
        if not refreshed:
            await reply_guess_result(update.message, guess)
        return

    try:
        result = duel.submit_secret_word(user.id, update.message.text)
    except duel.DuelError as exc:
        await update.message.reply_text(exc.message)
        return

    if result is None:
        return

    await announce_secret_result(update, context, result)
