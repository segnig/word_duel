"""Single in-chat game card — compact Wordle boards, HTML formatting."""

from word_duel.constants import ROLE_A, ROLE_B, STATUS_FINISHED, STATUS_IN_PROGRESS, STATUS_SETUP
from word_duel.game_logic import EMOJI, is_win
from word_duel.html import bold, code, esc, italic, spoiler


def format_draft(draft, length):
    draft = draft or ""
    cells = list(draft) + ["·"] * max(0, length - len(draft))
    return " ".join(cells)


def _tile_row(guess, feedback, hide_letters=False):
    parts = []
    for letter, color in zip(guess, feedback):
        shown = "•" if hide_letters else letter
        parts.append(f"{EMOJI[color]}{shown}")
    return " ".join(parts)


def _empty_slots(length):
    return " ".join("▫️" for _ in range(length))


def _player_header(game, role, is_turn):
    player = game["players"][role]
    used = player.get("guesses_made", 0)
    cap = game.get("max_rounds", 10)
    if player.get("solved"):
        mark = " ✓"
    elif is_turn and game["status"] == STATUS_IN_PROGRESS:
        mark = " ◀"
    else:
        mark = ""
    return f"{bold(player['name'])}{mark}   {code(f'{used}/{cap}')}"


def _player_board(game, role, is_turn):
    player = game["players"].get(role)
    if not player:
        return ""
    length = game["word_length"]
    rows = [entry for entry in game.get("history", []) if entry["role"] == role]
    hide_word = player.get("solved") and game["status"] == STATUS_IN_PROGRESS
    lines = [_player_header(game, role, is_turn)]
    if not rows:
        lines.append(_empty_slots(length))
    else:
        for entry in rows:
            hide = hide_word and is_win(entry["feedback"])
            lines.append(_tile_row(entry["guess"], entry["feedback"], hide_letters=hide))
    return "\n".join(lines)


def _vs_line(game):
    a = game["players"].get(ROLE_A, {}).get("name", "?")
    if ROLE_B not in game["players"]:
        return f"{bold(a)}  vs  {italic('waiting…')}"
    b = game["players"][ROLE_B]["name"]
    return f"{bold(a)}  vs  {bold(b)}"


def _header(game):
    length = game["word_length"]
    return f"⚔️ {bold('Word Duel')}  ·  {length} letters"


def _setup_body(game):
    lines = [_header(game), _vs_line(game), ""]
    if ROLE_B not in game["players"]:
        host = game["players"][ROLE_A]
        lines.append("①  Tap " + bold("Join") + " to play")
        lines.append("②  Each player sets a secret word")
        lines.append("③  Guess with the keyboard")
        lines.append("")
        if host.get("secret_word"):
            lines.append(f"{esc(host['name'])} — secret locked ✓")
        else:
            lines.append(italic("Host: tap letters, then Enter to lock your word."))
        return "\n".join(lines)

    lines.append(italic("Tap letters → Enter. Only you see your word (popup)."))
    lines.append("")
    for role in (ROLE_A, ROLE_B):
        player = game["players"][role]
        if player.get("secret_word"):
            lines.append(f"●  {esc(player['name'])}  ready ✓")
        else:
            lines.append(f"○  {esc(player['name'])}  picking a word…")
    return "\n".join(lines)


def _progress_body(game):
    turn = game["turn"]
    turn_player = game["players"][turn]
    a_solved = game["players"][ROLE_A].get("solved")
    b_solved = game["players"][ROLE_B].get("solved")
    lines = [_header(game), _vs_line(game), ""]
    if a_solved or b_solved:
        solver = game["players"][ROLE_A if a_solved else ROLE_B]
        lines.append(
            f"⚡ {esc(solver['name'])} found it — "
            f"{bold(turn_player['name'])} gets an equal guess"
        )
    else:
        lines.append(f"🎯  {bold(turn_player['name'])}'s turn")
    lines.append(italic("Letters stay on the keyboard. Hint is private (2 each)."))
    lines.append("")
    lines.append(_player_board(game, ROLE_A, is_turn=(turn == ROLE_A)))
    lines.append("")
    lines.append(_player_board(game, ROLE_B, is_turn=(turn == ROLE_B)))
    return "\n".join(lines)


def _finished_body(game):
    player_a = game["players"][ROLE_A]
    player_b = game["players"][ROLE_B]
    lines = [_header(game), _vs_line(game), ""]
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
    lines.append(_player_board(game, ROLE_A, is_turn=False))
    lines.append("")
    lines.append(_player_board(game, ROLE_B, is_turn=False))
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
