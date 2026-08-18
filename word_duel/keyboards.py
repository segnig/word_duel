from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from word_duel.constants import MODE_SOLO, ROLE_B, STATUS_FINISHED, STATUS_IN_PROGRESS, STATUS_SETUP

# 3 compact letter rows (A–Z) + 1 action row.
LETTER_ROWS = [
    list("ABCDEFGHI"),
    list("JKLMNOPQR"),
    list("STUVWXYZ"),
]


def join_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🙋  Join", callback_data="join")]])


def start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶  Play solo", callback_data="solo")],
        [InlineKeyboardButton("▶  Play with a friend", switch_inline_query="")],
        [InlineKeyboardButton("How to play", callback_data="help")],
    ])


def _letter_rows(include_hint=False):
    rows = [
        [InlineKeyboardButton(letter, callback_data=f"l:{letter}") for letter in row]
        for row in LETTER_ROWS
    ]
    actions = [InlineKeyboardButton("⌫", callback_data="bs")]
    if include_hint:
        actions.append(InlineKeyboardButton("💡", callback_data="hint"))
    actions.extend([
        InlineKeyboardButton("Enter", callback_data="ok"),
        InlineKeyboardButton("✕", callback_data="x"),
    ])
    rows.append(actions)
    return rows


def game_keyboard(game):
    rows = []
    status = game["status"]
    waiting = (
        status == STATUS_SETUP
        and ROLE_B not in game["players"]
        and game.get("mode") != MODE_SOLO
    )
    if waiting:
        rows.append([InlineKeyboardButton("🙋  Join game", callback_data="join")])
    if status in (STATUS_SETUP, STATUS_IN_PROGRESS):
        rows.extend(_letter_rows(include_hint=(status == STATUS_IN_PROGRESS)))
    if status == STATUS_FINISHED:
        rows.append([InlineKeyboardButton("🎉  Play again", callback_data="again")])
    return InlineKeyboardMarkup(rows)
