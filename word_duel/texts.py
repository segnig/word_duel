"""User-facing copy. Keep Telegram handlers free of long string literals."""


def start_help(bot_username="wordduelbot"):
    return (
        "👋 Word Duel works like @xoBot: one message, tap buttons.\n\n"
        f"In any chat, type @{bot_username} and send a Word Duel.\n"
        "Your friend taps Join, then both of you play on the letter buttons.\n"
        "Secret words stay hidden — only you see them in a popup.\n\n"
        "Or add me to a group and send /newduel."
    )


def players_line(game):
    players = game["players"]
    a = players.get("A", {}).get("name", "?")
    b = players.get("B", {}).get("name", "?")
    return f"{a} vs {b if 'B' in players else '(waiting for opponent)'}"


def game_already_active():
    return "There's already a game in progress in this chat. Use /cancel to abandon it first."


def new_duel_announcement(name, word_length):
    return (
        f"🎮 New Word Duel started by {name} ({word_length}-letter word)!\n"
        "Tap Join, then play on the buttons."
    )


def ask_for_secret_word(word_length):
    return (
        f"Send me your secret {word_length}-letter word for the duel. "
        "Only you will see this — it stays hidden from your opponent."
    )


def cannot_dm(name, bot_username):
    return (
        f"{name}, I can't DM you until you start a chat with me. "
        f"Tap here first, then send your word: https://t.me/{bot_username}"
    )


def both_players_joined(game):
    return (
        f"{players_line(game)}\n\n"
        "Both players: send /word YOURWORD in this chat (I'll delete it), "
        "or DM me the word privately."
    )


def both_players_ready(game):
    first = game["players"]["A"]["name"]
    return (
        f"⚔️ Both secret words are set! {players_line(game)}\n\n"
        f"{first}'s turn — type a word or use /guess WORD."
    )


def secret_locked_waiting_dm():
    return "Word locked in! Waiting for your opponent to submit theirs."


def secret_locked_waiting_group(name):
    return f"{name}'s word is locked in. Waiting for the other player."


def secret_locked_duel_started_dm():
    return "Word locked in! The duel has begun — check the group chat."


def could_not_hide_word():
    return (
        "I couldn't delete that message. Please delete it yourself so your "
        "opponent doesn't see the word, and make me a group admin with "
        "Delete messages."
    )


def word_usage(word_length):
    return f"Usage: /word YOURWORD  ({word_length} letters)"


def no_setup_for_word():
    return "No duel is waiting for secret words here. Use /newduel to start one."


def not_in_this_duel():
    return "You're not setting a word for this duel."


def invalid_word(word_length):
    return f"That's not a valid {word_length}-letter word (letters only). Try again."


def invalid_guess(word_length):
    return f"That's not a valid {word_length}-letter word (letters only)."


def no_active_duel():
    return "No duel in progress here. Use /newduel to start one."


def guess_usage(word_length):
    return f"Usage: /guess WORD  ({word_length} letters)"


def not_your_turn(name):
    return f"It's not your turn — waiting on {name}."


def win_message(board_text, winner_name, secret):
    return (
        f"{board_text}\n\n🎉 {winner_name} wins! The word was {secret}.\n"
        "Use /newduel to play again."
    )


def draw_message(board_text, player_a, player_b):
    return (
        f"{board_text}\n\n🤝 Out of guesses — it's a draw!\n"
        f"{player_a['name']}'s word was {player_a['secret_word']}. "
        f"{player_b['name']}'s word was {player_b['secret_word']}.\n"
        "Use /newduel to play again."
    )


def next_turn(board_text, name):
    return f"{board_text}\n\n{name}'s turn — type a word or use /guess WORD."


def no_game_to_cancel():
    return "No active game to cancel."


def only_players_can_cancel():
    return "Only a player in this game can cancel it."


def game_cancelled():
    return "Game cancelled."
