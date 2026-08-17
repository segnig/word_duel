"""Render the single in-chat game card, like @xoBot."""

from word_duel.constants import OTHER_ROLE, ROLE_A, ROLE_B, STATUS_FINISHED, STATUS_IN_PROGRESS, STATUS_SETUP
from word_duel.game_logic import render_feedback
from word_duel.texts import players_line


def format_draft(draft, length):
    draft = draft or ""
    cells = list(draft) + ["_"] * max(0, length - len(draft))
    return " ".join(cells)


def _player_board(game, role):
    player = game["players"].get(role)
    if not player:
        return ""
    lines = [player["name"]]
    rows = [entry for entry in game.get("history", []) if entry["role"] == role]
    if not rows:
        lines.append("· · ·")
    else:
        for entry in rows:
            lines.append(render_feedback(entry["guess"], entry["feedback"]))
    return "\n".join(lines)


def render_card(game):
    length = game["word_length"]
    lines = [
        f"🎮 Word Duel · {length} letters",
        "",
        players_line(game),
        "",
    ]
    status = game["status"]

    if status == STATUS_SETUP:
        if ROLE_B not in game["players"]:
            lines.append("Waiting for an opponent — tap Join.")
            host = game["players"][ROLE_A]
            if host.get("secret_word"):
                lines.append(f"{host['name']}: ready ✓")
            else:
                lines.append(f"{host['name']}: tap letters to set your secret word, then ✓")
        else:
            lines.append("Tap letters to set your secret word, then ✓")
            lines.append("Only you see the letters (popup). They stay hidden from your opponent.")
            for role in (ROLE_A, ROLE_B):
                player = game["players"][role]
                mark = "ready ✓" if player.get("secret_word") else "picking…"
                lines.append(f"{player['name']}: {mark}")

    elif status == STATUS_IN_PROGRESS:
        turn_player = game["players"][game["turn"]]
        lines.append(f"{turn_player['name']}'s turn — tap letters, then ✓")
        lines.append("")
        lines.append(_player_board(game, ROLE_A))
        lines.append("")
        lines.append(_player_board(game, ROLE_B))

    elif status == STATUS_FINISHED:
        if game.get("winner") == "draw":
            player_a, player_b = game["players"][ROLE_A], game["players"][ROLE_B]
            lines.append("🤝 Draw!")
            lines.append(f"{player_a['name']}'s word was {player_a['secret_word']}")
            lines.append(f"{player_b['name']}'s word was {player_b['secret_word']}")
        else:
            winner = game["players"][game["winner"]]
            opponent = game["players"][OTHER_ROLE[game["winner"]]]
            lines.append(f"🎉 {winner['name']} wins!")
            lines.append(f"The word was {opponent['secret_word']}")
        lines.append("")
        lines.append(_player_board(game, ROLE_A))
        lines.append("")
        lines.append(_player_board(game, ROLE_B))

    return "\n".join(lines).rstrip()
