from telegram import Update
from telegram.ext import ContextTypes

from word_duel import db, duel, texts
from word_duel.card import render_card
from word_duel.constants import STATUS_IN_PROGRESS, STATUS_SETUP
from word_duel.game_logic import is_valid_word, normalize_word
from word_duel.handlers.card import refresh_card
from word_duel.handlers.common import (
    announce_secret_result,
    reply_guess_result,
    try_hide_message,
)
from word_duel.keyboards import game_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = await context.bot.get_me()
    await update.message.reply_text(texts.start_help(me.username))


async def newduel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    word_length = duel.parse_word_length(context.args)

    try:
        game = duel.start_game(chat_id, user, word_length)
    except duel.DuelError as exc:
        await update.message.reply_text(exc.message)
        return

    sent = await update.message.reply_text(
        render_card(game),
        reply_markup=game_keyboard(game),
    )
    game["message_id"] = sent.message_id
    game["host_chat_id"] = chat_id
    db.save_game(game)


async def word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    in_group = chat.type in ("group", "supergroup")

    if in_group:
        game = db.get_game(chat.id)
        if not game or game["status"] != STATUS_SETUP:
            await update.message.reply_text(texts.no_setup_for_word())
            return
        if not context.args:
            await update.message.reply_text(texts.word_usage(game["word_length"]))
            return
        raw = context.args[0]
        if not is_valid_word(normalize_word(raw), game["word_length"]):
            await update.message.reply_text(texts.invalid_word(game["word_length"]))
            return
        hidden = await try_hide_message(update.message)
        try:
            result = duel.submit_secret_word(user.id, context.args[0])
        except duel.DuelError as exc:
            await chat.send_message(exc.message)
            return
        if result is None:
            await chat.send_message(texts.not_in_this_duel())
            return
        if not hidden:
            await chat.send_message(texts.could_not_hide_word())
        await refresh_card(result.game, bot=context.bot)
        return

    if not context.args:
        pending = db.get_pending(user.id)
        length = "n"
        if pending:
            pending_game = db.get_game(pending["chat_id"])
            if pending_game:
                length = pending_game["word_length"]
        await update.message.reply_text(texts.word_usage(length))
        return
    try:
        result = duel.submit_secret_word(user.id, context.args[0])
    except duel.DuelError as exc:
        await update.message.reply_text(exc.message)
        return
    if result is None:
        return
    await announce_secret_result(update, context, result)
    await refresh_card(result.game, bot=context.bot)


async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = db.get_game(chat_id)
    if not game or game["status"] != STATUS_IN_PROGRESS:
        await update.message.reply_text(texts.no_active_duel())
        return

    if not context.args:
        await update.message.reply_text(texts.guess_usage(game["word_length"]))
        return

    try:
        result = duel.make_guess(game, update.effective_user, context.args[0])
    except duel.DuelError as exc:
        await update.message.reply_text(exc.message)
        return

    refreshed = await refresh_card(result.game, bot=context.bot)
    if not refreshed:
        await reply_guess_result(update.message, result)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game = db.get_game(update.effective_chat.id)
    try:
        duel.cancel_game(game, update.effective_user.id)
    except duel.DuelError as exc:
        await update.message.reply_text(exc.message)
        return
    await update.message.reply_text(texts.game_cancelled())
