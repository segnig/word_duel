"""Parse @bot inline queries like 'CRANE', '6', or '6 MOUSE'."""

from word_duel.config import DEFAULT_WORD_LENGTH
from word_duel.constants import MAX_WORD_LENGTH, MIN_WORD_LENGTH
from word_duel.game_logic import is_valid_word, normalize_word


def parse_inline_query(text):
    """
    Returns (length, host_word, error).
    host_word is uppercase or None if the host will pick on the keyboard.
    """
    raw = (text or "").strip()
    if not raw:
        return DEFAULT_WORD_LENGTH, None, None

    parts = raw.split()
    length = None
    word = None
    idx = 0

    if parts[0].isdigit():
        length = int(parts[0])
        if not MIN_WORD_LENGTH <= length <= MAX_WORD_LENGTH:
            return DEFAULT_WORD_LENGTH, None, f"Length must be {MIN_WORD_LENGTH}–{MAX_WORD_LENGTH}."
        idx = 1

    if idx < len(parts):
        word = normalize_word(parts[idx] if len(parts) == idx + 1 else "".join(parts[idx:]))
        if not word.isalpha():
            return DEFAULT_WORD_LENGTH, None, "Use letters only."
        if length is None:
            length = len(word)
        elif len(word) != length:
            return length, None, f"Word must be exactly {length} letters."
        if not MIN_WORD_LENGTH <= length <= MAX_WORD_LENGTH:
            return DEFAULT_WORD_LENGTH, None, f"Length must be {MIN_WORD_LENGTH}–{MAX_WORD_LENGTH}."

    if length is None:
        length = DEFAULT_WORD_LENGTH

    if word and not is_valid_word(word, length):
        return length, None, f"Word must be {length} letters, letters only."

    return length, word, None
