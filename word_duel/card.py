"""Single in-chat game card — two-line guesses, clear turn / waiting."""

from word_duel.constants import (
    MODE_SOLO,
    OTHER_ROLE,
    ROLE_A,
    ROLE_B,
    STATUS_FINISHED,
    STATUS_IN_PROGRESS,
    STATUS_SETUP,
)
from word_duel.game_logic import EMOJI, GREEN, is_win, render_feedback
from word_duel.html import bold, code, esc, italic


PARTY = "🎉 🎊 🥳 ✨ 🏆 ✨ 🥳 🎊 🎉"
LOSS_ROW = "🌧️  💔  🌧️"
DRAW_ROW = "🤝  ✨  🤝"


def _cheer(guesses):
    """Wordle-style rank for how fast the word was found."""
    if guesses <= 1:
        return "🤯", "Genius"
    if guesses == 2:
        return "🔥", "Magnificent"
    if guesses == 3:
        return "🌟", "Impressive"
    if guesses == 4:
        return "🎉", "Splendid"
    if guesses == 5:
        return "🥳", "Great"
    if guesses == 6:
        return "👏", "Nice"
    if guesses <= 8:
        return "👍", "Good"
    return "😅", "Phew"


def format_draft(draft, length):
    draft = draft or ""
    cells = list(draft) + ["_"] * max(0, length - len(draft))
    return " ".join(cells)


def _is_solo(game):
    return game.get("mode") == MODE_SOLO


def _player_board(game, role):
    player = game["players"].get(role)
    if not player:
        return ""
    lines = [bold(player["name"])]
    if game["status"] == STATUS_FINISHED:
        winner = game.get("winner")
        if winner == role:
            lines[0] += "  🏆🎉  " + italic("winner")
        elif winner == "draw":
            lines[0] += "  🤝" if player.get("solved") else "  ·  " + italic("no")
        elif not player.get("solved"):
            lines[0] += "  💔  " + italic("lost")
        elif player.get("solved"):
            lines[0] += " ✓"
    elif player.get("solved"):
        lines[0] += " ✓"
    rows = [entry for entry in game.get("history", []) if entry["role"] == role]
    hide_word = player.get("solved") and game["status"] == STATUS_IN_PROGRESS
    if not rows:
        lines.append("· · ·")
    else:
        for entry in rows:
            if hide_word and is_win(entry["feedback"]):
                hidden = " ".join("•" for _ in entry["guess"])
                greens = "".join(EMOJI[GREEN] for _ in entry["guess"])
                lines.append(f"{hidden}\n{greens}")
            else:
                lines.append(render_feedback(entry["guess"], entry["feedback"]))
    return "\n".join(lines)


def _vs_line(game):
    a = game["players"].get(ROLE_A, {}).get("name", "?")
    if _is_solo(game):
        bot = game["players"].get(ROLE_B, {}).get("name", "Bot")
        return f"{bold(a)}  vs  {italic(bot)}  ·  solo"
    if ROLE_B not in game["players"]:
        return f"{bold(a)}  vs  {italic('waiting for opponent')}"
    b = game["players"][ROLE_B]["name"]
    return f"{bold(a)}  vs  {bold(b)}"


def _header(game):
    length = game["word_length"]
    if game["status"] == STATUS_FINISHED:
        return f"⚔️ {bold('Word Duel')}  ·  {length} letters  ·  result"
    return f"⚔️ {bold('Word Duel')}  ·  {length} letters"


def _round_line(game):
    a = game["players"].get(ROLE_A, {}).get("guesses_made", 0)
    b = game["players"].get(ROLE_B, {}).get("guesses_made", 0)
    cap = game.get("max_rounds", 10)
    if _is_solo(game):
        if game["status"] == STATUS_FINISHED:
            return f"Guess {a}/{cap}"
        guess_no = min(a + 1, cap) if a < cap else cap
        return f"Guess {guess_no}/{cap}"
    if game["status"] == STATUS_FINISHED:
        return f"Round {max(a, b)}/{cap}"
    if a == 0 and b == 0:
        round_no = 1
    elif a != b:
        round_no = max(a, b)
    else:
        round_no = min(a + 1, cap)
    return f"Round {round_no}/{cap}"


def _turn_block(game):
    """Whose turn it is and who is waiting."""
    if _is_solo(game):
        lines = [_round_line(game)]
        if game["status"] == STATUS_IN_PROGRESS:
            lines.append("▶ Your turn — guess the secret word")
        return "\n".join(lines)
    turn = game["turn"]
    playing = game["players"][turn]
    waiting = game["players"].get(OTHER_ROLE[turn])
    lines = [_round_line(game)]
    a_solved = game["players"][ROLE_A].get("solved")
    b_solved = game["players"][ROLE_B].get("solved")
    if a_solved or b_solved:
        solver = game["players"][ROLE_A if a_solved else ROLE_B]
        lines.append(f"⚡ {esc(solver['name'])} found the word")
        lines.append(f"▶ Playing: {bold(playing['name'])}  (equal chance)")
    else:
        lines.append(f"▶ Playing: {bold(playing['name'])}")
    if waiting:
        lines.append(f"⏳ Waiting: {esc(waiting['name'])}")
    return "\n".join(lines)


def _setup_body(game):
    lines = [_header(game), _vs_line(game), ""]
    if ROLE_B not in game["players"]:
        host = game["players"][ROLE_A]
        lines.append("▶ Playing: " + italic("waiting for opponent to join"))
        lines.append(f"⏳ Waiting: {esc(host['name'])} started the game")
        lines.append("")
        lines.append("①  Tap " + bold("Join") + " to play")
        lines.append("②  Each player sets a secret word")
        lines.append("③  Guess with the keyboard")
        lines.append("")
        if host.get("secret_word"):
            lines.append(f"{esc(host['name'])} — secret locked ✓")
        else:
            lines.append(italic("Host: tap letters, then Enter to lock your word."))
        return "\n".join(lines)

    picking = [p["name"] for p in game["players"].values() if not p.get("secret_word")]
    ready = [p["name"] for p in game["players"].values() if p.get("secret_word")]
    if picking:
        lines.append("▶ Playing: " + bold(", ".join(picking)) + " — set your secret word")
    if ready:
        lines.append("⏳ Waiting: " + ", ".join(esc(n) for n in ready) + " — ready ✓")
    lines.append("")
    lines.append(italic("Tap letters → Enter. Only you see your word (popup)."))
    return "\n".join(lines)


def _progress_body(game):
    lines = [
        _header(game),
        _vs_line(game),
        "",
        _turn_block(game),
        "",
        _player_board(game, ROLE_A),
    ]
    if not _is_solo(game):
        lines.extend(["", _player_board(game, ROLE_B)])
    return "\n".join(lines)


def _result_banner(game):
    cap = game.get("max_rounds", 10)
    a = game["players"][ROLE_A]
    b = game["players"][ROLE_B]
    if _is_solo(game):
        secret = b.get("secret_word") or "?"
        guesses = a.get("guesses_made", 0)
        if game.get("winner") == ROLE_A:
            emoji, title = _cheer(guesses)
            return [
                PARTY,
                "🏆  " + bold("YOU WIN"),
                f"{emoji}  " + bold(title),
                f"Found {code(secret)} in {bold(str(guesses))}/{cap} guesses",
                PARTY,
            ]
        return [
            LOSS_ROW,
            "💔  " + bold("YOU LOST"),
            f"The word was {code(secret)}",
            italic(f"😢  {guesses}/{cap} guesses used"),
            LOSS_ROW,
        ]

    winner = game.get("winner")
    if winner == "draw":
        if a.get("solved") and b.get("solved"):
            n = a.get("guesses_made", 0)
            return [
                DRAW_ROW,
                "🤝  " + bold("DRAW"),
                f"🎉  Both found the word in {n} guesses",
                DRAW_ROW,
            ]
        return [
            DRAW_ROW,
            "🤝  " + bold("DRAW"),
            italic("😢  Neither found the word"),
            DRAW_ROW,
        ]

    w = game["players"][winner]
    loser_role = OTHER_ROLE[winner]
    loser = game["players"][loser_role]
    found = loser.get("secret_word") or "?"
    guesses = w.get("guesses_made", 0)
    emoji, title = _cheer(guesses)
    return [
        PARTY,
        "🏆  " + bold("WINNER") + "   " + bold(w["name"]),
        f"{emoji}  " + bold(title),
        f"Found {code(found)} in {guesses} guesses",
        f"💔  {esc(loser['name'])}  ·  " + italic("lost"),
        PARTY,
    ]


def _secrets_block(game):
    a = game["players"][ROLE_A]
    b = game["players"][ROLE_B]
    if _is_solo(game):
        return []
    return [
        italic("Secrets"),
        f"{esc(a['name'])}  {code(a.get('secret_word'))}",
        f"{esc(b['name'])}  {code(b.get('secret_word'))}",
    ]


def _finished_body(game):
    lines = [_header(game), _vs_line(game), "", *_result_banner(game), ""]
    secrets = _secrets_block(game)
    if secrets:
        lines.extend(secrets)
        lines.append("")
    lines.append(_player_board(game, ROLE_A))
    if not _is_solo(game):
        lines.extend(["", _player_board(game, ROLE_B)])
    return "\n".join(lines)


def render_card(game):
    status = game["status"]
    if status == STATUS_SETUP:
        return _setup_body(game)
    if status == STATUS_IN_PROGRESS:
        return _progress_body(game)
    if status == STATUS_FINISHED:
        return _finished_body(game)
    return _header(game)
