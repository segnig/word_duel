from telegram.ext import ContextTypes

from word_duel import duel
from word_duel.handlers.common import announce_secret_result


async def handle_private_message(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        result = duel.submit_secret_word(user.id, update.message.text)
    except duel.DuelError as exc:
        await update.message.reply_text(exc.message)
        return

    if result is None:
        return

    await announce_secret_result(update, context, result)
