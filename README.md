# Word Duel Bot

Two-player secret-word guessing bot for Telegram, backed by MongoDB.
See `docs/design.md` for the full game design.

## Layout

```
bot.py                     # entry point — python bot.py
word_duel/
  app.py                   # Telegram application + polling
  config.py                # env-based settings
  constants.py             # statuses, roles, word-length bounds
  duel.py                  # game flow (start, join, guess, cancel)
  game_logic.py            # Wordle scoring / word validation
  db.py                    # MongoDB access
  texts.py                 # user-facing copy
  keyboards.py             # inline buttons
  handlers/                # Telegram command / callback / DM handlers
docs/design.md             # game design
```

Add new commands in `word_duel/handlers/`, game rules in `duel.py` / `game_logic.py`,
and copy in `texts.py`.

## Setup

1. **MongoDB** — have a MongoDB instance reachable (local install, Docker,
   or Atlas free tier all work):
   ```bash
   docker run -d -p 27017:27017 --name word-duel-mongo mongo
   ```

2. **Bot token** — message [@BotFather](https://t.me/BotFather) on Telegram,
   run `/newbot`, and copy the token.

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables and run:**
   ```bash
   export BOT_TOKEN="123456:ABC-your-token"
   export MONGO_URI="mongodb://localhost:27017"   # optional, this is the default
   python bot.py
   ```

   Copy `.env.example` if you prefer a local env file (load it yourself, or
   export the variables). You can also run `python -m word_duel`.

## Playing

1. Add the bot to a **group chat** and make it admin with **Delete messages**
   so it can hide secret words. In [@BotFather](https://t.me/BotFather) run
   `/setprivacy` → Disable so the bot can see typed words (not only commands).
2. In the group: `/newduel` (optionally `/newduel 6` for a 6-letter word).
3. Second player taps **Join game**.
4. Both players set a secret word **in the group**: `/word CRANE`
   (the bot deletes that message). You can also type the word, or DM it.
5. Once both words are in, guess **in the group**: type `HOUSE` on your turn
   or use `/guess HOUSE`. The bot posts color-coded feedback.
6. First exact match wins. If both players use all their guesses
   (10 by default) with no winner, it's a draw and both words are revealed.
7. `/cancel` lets either player abandon an in-progress game.

## Notes / things you may want to extend

- **Dictionary validation**: `word_duel.game_logic.is_valid_word` currently only
  checks length + letters-only. Plug in a word list there if you want to reject
  non-words.
- **Timeouts**: there's no auto-forfeit for an inactive player yet — you'd
  add a `last_action_at` timestamp to the game doc and a periodic job
  (`JobQueue` in python-telegram-bot) to check it.
- **Rematch button**: `/newduel` right after a finished game works today;
  a one-tap "Play again" button reusing the same two players would wrap
  `duel.start_game`.
- **Scaling to many concurrent games**: this already supports one game per
  chat concurrently since games are keyed by `chat_id` in Mongo — no changes
  needed for many *groups* to play simultaneously.
