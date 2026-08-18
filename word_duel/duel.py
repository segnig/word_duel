"""
Game orchestration: start, join, secret-word submit, guess, cancel.

Handlers talk to this module instead of mutating Mongo documents directly,
so new features (dictionary, rematch, timeouts) can plug in here.
"""
from dataclasses import dataclass

from word_duel import db
from word_duel.config import DEFAULT_MAX_ROUNDS, DEFAULT_WORD_LENGTH
from word_duel.constants import (
    MAX_HINTS,
    MAX_WORD_LENGTH,
    MIN_WORD_LENGTH,
    OTHER_ROLE,
    ROLE_A,
    ROLE_B,
    STATUS_FINISHED,
    STATUS_IN_PROGRESS,
    STATUS_SETUP,
)
from word_duel.game_logic import (
    evaluate_guess,
    is_valid_word,
    is_win,
    next_hint,
    normalize_word,
    render_feedback,
)
from word_duel import texts


class DuelError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


@dataclass
class SecretSubmitResult:
    waiting_for_opponent: bool
    game: dict


@dataclass
class GuessResult:
    kind: str  # win | draw | next | reply
    board_text: str
    game: dict


@dataclass
class HintResult:
    position: int
    letter: str
    used: int
    remaining: int


def parse_word_length(args):
    word_length = DEFAULT_WORD_LENGTH
    if not args:
        return word_length
    try:
        candidate = int(args[0])
    except (TypeError, ValueError):
        return word_length
    if MIN_WORD_LENGTH <= candidate <= MAX_WORD_LENGTH:
        return candidate
    return word_length


def _new_player(user):
    return {
        "user_id": user.id,
        "name": user.first_name,
        "secret_word": None,
        "guesses_made": 0,
        "solved": False,
        "hints_used": 0,
    }


def _player_history(game, role):
    return [entry for entry in game.get("history", []) if entry["role"] == role]


def _finish(game, winner, board_text, kind):
    game["status"] = STATUS_FINISHED
    game["winner"] = winner
    db.save_game(game)
    return GuessResult(kind=kind, board_text=board_text, game=game)


def role_for_user(game, user_id):
    if not game:
        return None
    for role, player in game["players"].items():
        if player["user_id"] == user_id:
            return role
    return None


def start_game(chat_id, user, word_length=None, host_word=None):
    existing = db.get_game(chat_id)
    if existing and existing["status"] != STATUS_FINISHED:
        raise DuelError(texts.game_already_active())

    if word_length is None:
        word_length = DEFAULT_WORD_LENGTH

    game = db.create_game(chat_id, word_length, DEFAULT_MAX_ROUNDS)
    game["players"][ROLE_A] = _new_player(user)
    if host_word:
        host_word = normalize_word(host_word)
        if not is_valid_word(host_word, word_length):
            raise DuelError(texts.invalid_word(word_length))
        game["players"][ROLE_A]["secret_word"] = host_word
    else:
        db.set_pending(user.id, chat_id, ROLE_A)
    db.save_game(game)
    return game


def join_game(game, user):
    if game["status"] != STATUS_SETUP or ROLE_B in game["players"]:
        raise DuelError("Game is already full or in progress.")
    if user.id == game["players"][ROLE_A]["user_id"]:
        raise DuelError("You already started this game — wait for an opponent.")

    game["players"][ROLE_B] = _new_player(user)
    db.save_game(game)
    db.set_pending(user.id, game["_id"], ROLE_B)
    return game


def submit_secret_word(user_id, raw_word):
    pending = db.get_pending(user_id)
    if not pending:
        return None

    game = db.get_game(pending["chat_id"])
    if not game or game["status"] != STATUS_SETUP:
        db.clear_pending(user_id)
        return None

    word = normalize_word(raw_word)
    if not is_valid_word(word, game["word_length"]):
        raise DuelError(texts.invalid_word(game["word_length"]))

    role = pending["role"]
    game["players"][role]["secret_word"] = word
    db.clear_pending(user_id)

    both_ready = (
        len(game["players"]) == 2
        and all(player.get("secret_word") for player in game["players"].values())
    )
    if both_ready:
        game["status"] = STATUS_IN_PROGRESS

    db.save_game(game)
    return SecretSubmitResult(waiting_for_opponent=not both_ready, game=game)


def make_guess(game, user, raw_word):
    if not game or game["status"] != STATUS_IN_PROGRESS:
        raise DuelError(texts.no_active_duel())

    turn = game["turn"]
    active_player = game["players"][turn]
    if user.id != active_player["user_id"]:
        raise DuelError(texts.not_your_turn(active_player["name"]))

    guess_word = normalize_word(raw_word)
    if not is_valid_word(guess_word, game["word_length"]):
        raise DuelError(texts.invalid_guess(game["word_length"]))

    opponent_role = OTHER_ROLE[turn]
    opponent = game["players"][opponent_role]
    feedback = evaluate_guess(opponent["secret_word"], guess_word)

    game["history"].append({
        "role": turn,
        "name": active_player["name"],
        "guess": guess_word,
        "feedback": feedback,
    })
    active_player["guesses_made"] += 1
    if is_win(feedback):
        active_player["solved"] = True
    board_text = render_feedback(guess_word, feedback)

    player_a = game["players"][ROLE_A]
    player_b = game["players"][ROLE_B]
    a_guesses = player_a["guesses_made"]
    b_guesses = player_b["guesses_made"]
    a_solved = player_a.get("solved", False)
    b_solved = player_b.get("solved", False)

    # Equal chances: if someone solved and the other has fewer guesses, they reply.
    if a_solved or b_solved:
        if a_guesses != b_guesses:
            trailing = ROLE_A if a_guesses < b_guesses else ROLE_B
            game["turn"] = trailing
            db.save_game(game)
            return GuessResult(kind="reply", board_text=board_text, game=game)
        if a_solved and b_solved:
            return _finish(game, "draw", board_text, "draw")
        winner = ROLE_A if a_solved else ROLE_B
        return _finish(game, winner, board_text, "win")

    both_maxed = a_guesses >= game["max_rounds"] and b_guesses >= game["max_rounds"]
    if both_maxed:
        return _finish(game, "draw", board_text, "draw")

    game["turn"] = opponent_role
    db.save_game(game)
    return GuessResult(kind="next", board_text=board_text, game=game)


def use_hint(game, user):
    if not game or game["status"] != STATUS_IN_PROGRESS:
        raise DuelError(texts.no_active_duel())
    role = _require_player(game, user)
    player = game["players"][role]
    used = player.get("hints_used", 0)
    if used >= MAX_HINTS:
        raise DuelError(texts.no_hints_left())
    if player.get("solved"):
        raise DuelError("You already found the word.")

    opponent = game["players"][OTHER_ROLE[role]]
    hint = next_hint(opponent["secret_word"], _player_history(game, role))
    if not hint:
        raise DuelError("No hint left — you already know every letter.")

    player["hints_used"] = used + 1
    db.save_game(game)
    position, letter = hint
    return HintResult(
        position=position,
        letter=letter,
        used=player["hints_used"],
        remaining=MAX_HINTS - player["hints_used"],
    )


def cancel_game(game, user_id):
    if not game or game["status"] == STATUS_FINISHED:
        raise DuelError(texts.no_game_to_cancel())

    player_ids = [player["user_id"] for player in game["players"].values()]
    if user_id not in player_ids:
        raise DuelError(texts.only_players_can_cancel())

    db.delete_game(game["_id"])


def _drafts(game):
    game.setdefault("drafts", {"A": "", "B": ""})
    game["drafts"].setdefault("A", "")
    game["drafts"].setdefault("B", "")
    return game["drafts"]


def _require_player(game, user):
    if not game:
        raise DuelError(texts.no_active_duel())
    role = role_for_user(game, user.id)
    if not role:
        raise DuelError("You're not in this game.")
    if user.first_name:
        game["players"][role]["name"] = user.first_name
    return role


def _require_can_type(game, role):
    if game["status"] == STATUS_FINISHED:
        raise DuelError("This game is over. Tap Play again.")
    if game["status"] == STATUS_SETUP:
        if game["players"][role].get("secret_word"):
            raise DuelError("Your word is already locked in.")
        return
    if game["status"] == STATUS_IN_PROGRESS:
        if game["turn"] != role:
            raise DuelError(texts.not_your_turn(game["players"][game["turn"]]["name"]))
        return
    raise DuelError("You can't type right now.")


def add_letter(game, user, letter):
    letter = (letter or "").upper()
    if len(letter) != 1 or not letter.isalpha():
        raise DuelError("Invalid letter.")
    role = _require_player(game, user)
    _require_can_type(game, role)
    drafts = _drafts(game)
    if len(drafts[role]) >= game["word_length"]:
        return drafts[role]
    drafts[role] += letter
    db.save_game(game)
    return drafts[role]


def backspace_draft(game, user):
    role = _require_player(game, user)
    _require_can_type(game, role)
    drafts = _drafts(game)
    drafts[role] = drafts[role][:-1]
    db.save_game(game)
    return drafts[role]


def confirm_draft(game, user):
    role = _require_player(game, user)
    draft = _drafts(game).get(role, "")

    if game["status"] == STATUS_SETUP:
        if game["players"][role].get("secret_word"):
            raise DuelError("Your word is already locked in.")
        if not is_valid_word(draft, game["word_length"]):
            raise DuelError(f"Need {game['word_length']} letters.")
        game["players"][role]["secret_word"] = draft
        game["drafts"][role] = ""
        db.clear_pending(user.id)
        both_ready = (
            len(game["players"]) == 2
            and all(player.get("secret_word") for player in game["players"].values())
        )
        if both_ready:
            game["status"] = STATUS_IN_PROGRESS
        db.save_game(game)
        return SecretSubmitResult(waiting_for_opponent=not both_ready, game=game)

    if game["status"] != STATUS_IN_PROGRESS:
        raise DuelError("This game is over. Tap Play again.")

    if not is_valid_word(draft, game["word_length"]):
        raise DuelError(f"Need {game['word_length']} letters.")

    result = make_guess(game, user, draft)
    result.game.setdefault("drafts", {})[role] = ""
    db.save_game(result.game)
    return result


def rematch(game, user):
    if not game or game["status"] != STATUS_FINISHED:
        raise DuelError("No finished game to rematch.")
    _require_player(game, user)
    for player in game["players"].values():
        player["secret_word"] = None
        player["guesses_made"] = 0
        player["solved"] = False
        player["hints_used"] = 0
    game["status"] = STATUS_SETUP
    game["turn"] = ROLE_A
    game["history"] = []
    game["winner"] = None
    game["drafts"] = {"A": "", "B": ""}
    db.save_game(game)
    for role, player in game["players"].items():
        db.set_pending(player["user_id"], game["_id"], role)
    return game
