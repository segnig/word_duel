from types import SimpleNamespace

from telegram import Update
from telegram.ext import ContextTypes

from word_duel import db, duel, texts
from word_duel.card import format_draft, render_card
from word_duel.config import DEFAULT_WORD_LENGTH
from word_duel.constants import ROLE_A, ROLE_B
from word_duel.html import PARSE_MODE
from word_duel.handlers.card import game_id_from_query, refresh_card
from word_duel.keyboards import game_keyboard


async def _load_game(query):
    game_id = game_id_from_query(query)
    if game_id is None:
        return None
    return db.get_game(game_id)


def _parse_join(data):
    if data == "join":
        return None, DEFAULT_WORD_LENGTH, None
    parts = data.split(":")
    host_id = int(parts[1]) if len(parts) > 1 and parts[1].lstrip("-").isdigit() else None
    length = DEFAULT_WORD_LENGTH
    if len(parts) > 2 and parts[2].isdigit():
        length = int(parts[2])
    host_word = parts[3].upper() if len(parts) > 3 else None
    return host_id, length, host_word


async def _ensure_inline_game(query, data):
    """Create the inline game if ChosenInlineResult hasn't landed yet."""
    game = await _load_game(query)
    if game or not query.inline_message_id:
        return game
    host_id, length, host_word = _parse_join(data)
    if host_id is None:
        host_id = query.from_user.id
    game_id = f"inline:{query.inline_message_id}"
    if query.from_user.id == host_id:
        host = query.from_user
    else:
        host = SimpleNamespace(id=host_id, first_name="Player")
    game = duel.start_game(game_id, host, length, host_word=host_word)
    game["inline_message_id"] = query.inline_message_id
    db.save_game(game)
    return game


async def handle_solo(query, context):
    message = query.message
    if not message or message.chat.type != "private":
        await query.answer("Open a private chat with me and send /newduel.", show_alert=True)
        return
    bot_name = (context.bot.first_name or "Bot").strip()
    try:
        game = duel.start_solo_game(
            message.chat.id,
            query.from_user,
            DEFAULT_WORD_LENGTH,
            bot_name,
        )
    except duel.DuelError as exc:
        await query.answer(exc.message, show_alert=True)
        return
    await query.answer("Solo game started — guess the word.")
    sent = await message.reply_text(
        render_card(game),
        reply_markup=game_keyboard(game),
        parse_mode=PARSE_MODE,
    )
    game["message_id"] = sent.message_id
    game["host_chat_id"] = message.chat.id
    db.save_game(game)


async def handle_join(query, game):
    try:
        game = duel.join_game(game, query.from_user)
    except duel.DuelError as exc:
        await query.answer(exc.message, show_alert=True)
        return
    await query.answer(f"{query.from_user.first_name} joined!")
    await refresh_card(game, query=query)


async def handle_letter(query, game, letter):
    try:
        draft = duel.add_letter(game, query.from_user, letter)
    except duel.DuelError as exc:
        await query.answer(exc.message, show_alert=True)
        return
    await query.answer(format_draft(draft, game["word_length"]))


async def handle_backspace(query, game):
    try:
        draft = duel.backspace_draft(game, query.from_user)
    except duel.DuelError as exc:
        await query.answer(exc.message, show_alert=True)
        return
    await query.answer(format_draft(draft, game["word_length"]))


async def handle_confirm(query, game):
    try:
        result = duel.confirm_draft(game, query.from_user)
    except duel.DuelError as exc:
        await query.answer(exc.message, show_alert=True)
        return

    if isinstance(result, duel.SecretSubmitResult):
        if result.waiting_for_opponent:
            await query.answer("Word locked in. Waiting for opponent.")
        else:
            await query.answer("Both words set — duel started!")
        await refresh_card(result.game, query=query)
        return

    if result.kind in ("win", "loss", "draw"):
        await query.answer(
            texts.finish_alert(result.kind, result.game, query.from_user.id),
            show_alert=True,
        )
    elif result.kind == "reply":
        await query.answer("Correct! Opponent gets an equal chance.")
    else:
        await query.answer("Guess posted.")
    await refresh_card(result.game, query=query)


async def handle_hint(query, game):
    try:
        hint = duel.use_hint(game, query.from_user)
    except duel.DuelError as exc:
        await query.answer(exc.message, show_alert=True)
        return
    await query.answer(
        texts.hint_popup(hint.position, hint.letter, hint.used, hint.remaining),
        show_alert=True,
    )


async def handle_help(query):
    if query.message:
        await query.answer()
        await query.message.reply_text(texts.how_to_play(), parse_mode=PARSE_MODE)
        return
    await query.answer("Open the bot and send /start for how to play.", show_alert=True)


async def handle_cancel_button(query, game):
    try:
        duel.cancel_game(game, query.from_user.id)
    except duel.DuelError as exc:
        await query.answer(exc.message, show_alert=True)
        return
    await query.answer("Game ended.")
    await query.edit_message_text("✕  Game ended.")


async def handle_rematch(query, game):
    try:
        game = duel.rematch(game, query.from_user)
    except duel.DuelError as exc:
        await query.answer(exc.message, show_alert=True)
        return
    if duel.is_solo(game):
        await query.answer("🎉 New word. Good luck!")
    else:
        await query.answer("Play again — lock your secret words.")
    await refresh_card(game, query=query)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    if data == "help":
        await handle_help(query)
        return
    if data == "solo":
        await handle_solo(query, context)
        return
    game = await _load_game(query)
    if not game and (data == "join" or data.startswith("join:")):
        try:
            game = await _ensure_inline_game(query, data)
        except duel.DuelError as exc:
            await query.answer(exc.message, show_alert=True)
            return
    if not game:
        await query.answer("No active game. Send a new one with @bot or /newduel.", show_alert=True)
        return

    if data == "join" or data.startswith("join:"):
        if (
            duel.role_for_user(game, query.from_user.id) == ROLE_A
            and ROLE_B not in game["players"]
        ):
            game["players"][ROLE_A]["name"] = query.from_user.first_name
            db.save_game(game)
            await query.answer("Waiting for an opponent.")
            await refresh_card(game, query=query)
            return
        await handle_join(query, game)
    elif data.startswith("l:") and len(data) == 3:
        await handle_letter(query, game, data[2])
    elif data == "bs":
        await handle_backspace(query, game)
    elif data == "ok":
        await handle_confirm(query, game)
    elif data == "hint":
        await handle_hint(query, game)
    elif data == "x":
        await handle_cancel_button(query, game)
    elif data == "again":
        await handle_rematch(query, game)
    else:
        await query.answer()
