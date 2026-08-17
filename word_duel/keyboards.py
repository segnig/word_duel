from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from word_duel.constants import ROLE_B, STATUS_FINISHED, STATUS_IN_PROGRESS, STATUS_SETUP

LETTER_ROWS = [
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
]


def join_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Join game", callback_data="join")]])


def _letter_rows():
    rows = [
        [InlineKeyboardButton(letter, callback_data=f"l:{letter}") for letter in row]
        for row in LETTER_ROWS
    ]
    rows.append([
        InlineKeyboardButton("⌫", callback_data="bs"),
        InlineKeyboardButton("✓", callback_data="ok"),
    ])
    return rows


def game_keyboard(game):
    rows = []
    status = game["status"]
    if status == STATUS_SETUP and ROLE_B not in game["players"]:
        rows.append([InlineKeyboardButton("Join game", callback_data="join")])
    if status in (STATUS_SETUP, STATUS_IN_PROGRESS):
        rows.extend(_letter_rows())
        rows.append([InlineKeyboardButton("Cancel", callback_data="x")])
    if status == STATUS_FINISHED:
        rows.append([InlineKeyboardButton("Play again", callback_data="again")])
    return InlineKeyboardMarkup(rows)
