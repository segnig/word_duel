"""
Pure game logic — no Telegram or database imports here, so it's easy to
unit test in isolation. Plug a dictionary into `is_valid_word` later if
you want strict valid-word-only enforcement.
"""

GREEN, YELLOW, GRAY = "green", "yellow", "gray"
EMOJI = {GREEN: "🟩", YELLOW: "🟨", GRAY: "⬜"}


def normalize_word(text):
    return (text or "").strip().upper()


def is_valid_word(word, length):
    """Letters only, exact length."""
    return isinstance(word, str) and len(word) == length and word.isalpha()


def evaluate_guess(secret, guess):
    """
    Return a list of 'green' / 'yellow' / 'gray', one per letter of `guess`,
    scored against `secret`. Both must be same length, uppercase.
    Handles duplicate letters the standard Wordle way: greens are resolved
    first and consume their letter from the pool before yellows are assigned.
    """
    n = len(secret)
    result = [GRAY] * n
    remaining = {}

    for i in range(n):
        if guess[i] == secret[i]:
            result[i] = GREEN
        else:
            remaining[secret[i]] = remaining.get(secret[i], 0) + 1

    for i in range(n):
        if result[i] == GREEN:
            continue
        letter = guess[i]
        if remaining.get(letter, 0) > 0:
            result[i] = YELLOW
            remaining[letter] -= 1

    return result


def render_feedback(guess, feedback):
    """Two-line display: the guessed letters, then the color row."""
    letters_row = " ".join(guess)
    colors_row = "".join(EMOJI[f] for f in feedback)
    return f"{letters_row}\n{colors_row}"


def is_win(feedback):
    return all(f == GREEN for f in feedback)


def unknown_letter_positions(secret, history_for_player):
    """Positions in `secret` this player has not yet scored as green."""
    known = set()
    for entry in history_for_player or []:
        for i, color in enumerate(entry.get("feedback") or []):
            if color == GREEN:
                known.add(i)
    return [i for i in range(len(secret)) if i not in known]


def next_hint(secret, history_for_player):
    """Reveal the first still-unknown letter (1-based position)."""
    unknown = unknown_letter_positions(secret, history_for_player)
    if not unknown:
        return None
    index = unknown[0]
    return index + 1, secret[index]
