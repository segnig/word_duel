"""Shared game constants. Keep Telegram and Mongo out of this file."""

STATUS_SETUP = "SETUP"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_FINISHED = "FINISHED"

MODE_DUEL = "duel"
MODE_SOLO = "solo"

ROLE_A = "A"
ROLE_B = "B"
OTHER_ROLE = {ROLE_A: ROLE_B, ROLE_B: ROLE_A}

BOT_USER_ID = 0

MIN_WORD_LENGTH = 3
MAX_WORD_LENGTH = 8

MAX_HINTS = 2
