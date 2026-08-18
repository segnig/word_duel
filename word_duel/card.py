"""Single in-chat game card — two-line guesses, clear turn / waiting."""

from word_duel.constants import (
    OTHER_ROLE,
    ROLE_A,
    ROLE_B,
    STATUS_FINISHED,
    STATUS_IN_PROGRESS,
    STATUS_SETUP,
)
from word_duel.game_logic import EMOJI, GREEN, is_win, render_feedback
from word_duel.html import bold, esc, italic, spoiler


def format_draft(draft, length):
    draft = draft or ""
    cells = list(draft) + ["_"] * max(0, length - len(draft))
    return " ".join(cells)


def _player_board(game, role):
    player = game["players"].get(role)
    if not player:
        return ""
    lines = [bold(player["name"])]
    if player.get("solved"):
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
    if ROLE_B not in game["players"]:
        return f"{bold(a)}  vs  {italic('waiting for opponent')}"
    b = game["players"][ROLE_B]["name"]
    return f"{bold(a)}  vs  {bold(b)}"


def _header(game):
    length = game["word_length"]
    return f"⚔️ {bold('Word Duel')}  ·  {length} letters"


def _round_line(game):
    a = game["players"].get(ROLE_A, {}).get("guesses_made", 0)
    b = game["players"].get(ROLE_B, {}).get("guesses_made", 0)
    cap = game.get("max_rounds", 10)
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
    return "\n".join([
        _header(game),
        _vs_line(game),
        "",
        _turn_block(game),
        "",
        _player_board(game, ROLE_A),
        "",
        _player_board(game, ROLE_B),
    ])


def _finished_body(game):
    player_a = game["players"][ROLE_A]
    player_b = game["players"][ROLE_B]
    lines = [_header(game), _vs_line(game), "", _round_line(game), ""]
    if game.get("winner") == "draw":
        if player_a.get("solved") and player_b.get("solved"):
            lines.append("🤝  " + bold("Draw") + " — same number of guesses")
        else:
            lines.append("🤝  " + bold("Draw") + " — out of guesses")
    else:
        winner = game["players"][game["winner"]]
        lines.append(f"🏆  {bold(winner['name'])} wins")
    lines.append("")
    lines.append(f"{esc(player_a['name'])}  {spoiler(player_a['secret_word'])}")
    lines.append(f"{esc(player_b['name'])}  {spoiler(player_b['secret_word'])}")
    lines.append(italic("Tap a word to reveal."))
    lines.append("")
    lines.append(_player_board(game, ROLE_A))
    lines.append("")
    lines.append(_player_board(game, ROLE_B))
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
