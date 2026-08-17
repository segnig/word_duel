from telegram.error import Forbidden

from word_duel import texts
from word_duel.constants import OTHER_ROLE


async def try_hide_message(message):
    """Delete a group message so a secret word is not left visible."""
    try:
        await message.delete()
        return True
    except Exception:
        return False


async def try_dm_for_word(context, user_id, name, word_length):
    """Optional DM prompt. Group /word still works if this fails."""
    try:
        await context.bot.send_message(user_id, texts.ask_for_secret_word(word_length))
        return True
    except Forbidden:
        return False


async def reply_guess_result(message, result):
    players = result.game["players"]
    if result.kind == "win":
        winner = players[result.game["winner"]]
        opponent = players[OTHER_ROLE[result.game["winner"]]]
        await message.reply_text(
            texts.win_message(result.board_text, winner["name"], opponent["secret_word"])
        )
        return

    if result.kind == "draw":
        await message.reply_text(
            texts.draw_message(result.board_text, players["A"], players["B"])
        )
        return

    next_player = players[result.game["turn"]]
    await message.reply_text(texts.next_turn(result.board_text, next_player["name"]))


async def announce_secret_result(update, context, result):
    chat = update.effective_chat
    user = update.effective_user
    in_private = chat.type == "private"

    if result.waiting_for_opponent:
        if in_private:
            await update.message.reply_text(texts.secret_locked_waiting_dm())
        else:
            await chat.send_message(texts.secret_locked_waiting_group(user.first_name))
        return

    if in_private:
        await update.message.reply_text(texts.secret_locked_duel_started_dm())
        await context.bot.send_message(result.game["_id"], texts.both_players_ready(result.game))
        return

    await chat.send_message(texts.both_players_ready(result.game))
