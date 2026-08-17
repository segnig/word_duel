from telegram import Update
from telegram.ext import ContextTypes

from word_duel import db, duel, texts
from word_duel.card import format_draft
from word_duel.handlers.card import game_id_from_query, refresh_card


async def _load_game(query):
    game_id = game_id_from_query(query)
    if game_id is None:
        return None
    return db.get_game(game_id)


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

    await query.answer("Guess posted.")
    await refresh_card(result.game, query=query)


async def handle_cancel_button(query, game):
    try:
        duel.cancel_game(game, query.from_user.id)
    except duel.DuelError as exc:
        await query.answer(exc.message, show_alert=True)
        return
    await query.answer("Game cancelled.")
    await query.edit_message_text(texts.game_cancelled())


async def handle_rematch(query, game):
    try:
        game = duel.rematch(game, query.from_user)
    except duel.DuelError as exc:
        await query.answer(exc.message, show_alert=True)
        return
    await query.answer("New duel — set your secret words.")
    await refresh_card(game, query=query)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    game = await _load_game(query)
    if not game:
        await query.answer("No active game. Send a new one with @bot or /newduel.", show_alert=True)
        return

    if data == "join":
        await handle_join(query, game)
    elif data.startswith("l:") and len(data) == 3:
        await handle_letter(query, game, data[2])
    elif data == "bs":
        await handle_backspace(query, game)
    elif data == "ok":
        await handle_confirm(query, game)
    elif data == "x":
        await handle_cancel_button(query, game)
    elif data == "again":
        await handle_rematch(query, game)
    else:
        await query.answer()
