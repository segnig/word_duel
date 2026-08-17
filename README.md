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
  card.py                   # one-message game board (xoBot-style)
  keyboards.py             # join + letter pad
  handlers/                # commands, callbacks, inline, DM
docs/design.md             # game design
```

Add new commands in `word_duel/handlers/`, game rules in `duel.py` / `game_logic.py`,
and copy in `texts.py`.

## Setup

### 1. MongoDB Atlas (recommended)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and create a free account.
2. Create a **free cluster** (M0).
3. **Database Access** → Add user → set username + password (save the password).
4. **Network Access** → Add IP Address:
   - For development: **Allow Access from Anywhere** (`0.0.0.0/0`)
   - For production: add your server's IP only.
5. **Database** → **Connect** → **Drivers** → copy the connection string.
6. Replace `<password>` with your user's password (URL-encode special chars like `@` → `%40`).

### 2. Bot token

Message [@BotFather](https://t.me/BotFather) on Telegram, run `/newbot`, and copy the token.

### 3. Inline mode (required, like @xoBot)

In BotFather:
- `/setinline` → enable, placeholder e.g. `CRANE or 6 MONKEY`
- `/setinlinefeedback` → **Enable**

### 4. Install and configure

```bash
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```bash
BOT_TOKEN=123456:ABC-your-telegram-token
MONGO_URI=mongodb+srv://myuser:mypassword@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=word_duel
```

### 5. Run

```bash
python bot.py
```

You should see `MongoDB connected (Atlas)` then the bot starts polling.

**Local MongoDB instead?** Use `MONGO_URI=mongodb://localhost:27017` or Docker:
```bash
docker run -d -p 27017:27017 --name word-duel-mongo mongo
```

## Playing

Works like [@xoBot](https://t.me/xoBot): one message, tap buttons. No need to
type guesses in the chat.

1. Open the bot and tap **Play in a chat**, or in any chat type
   `@YourBot` followed by your word:
   - `@YourBot CRANE` — 5 letters, your secret word is CRANE
   - `@YourBot 6 MONKEY` — 6 letters, your word is MONKEY
   - `@YourBot 6` — 6 letters, pick your word on the buttons
2. Your friend taps **Join game** on that message.
3. Friend sets their secret word on the letter buttons, then **✓**.
4. Take turns tapping a guess + **✓**. The same message updates with
   Wordle-style colors.
5. First exact match wins. **Play again** starts a rematch with the same two players.

You can also add the bot to a group and send `/newduel` (or `/newduel 6`).
`/cancel` or the Cancel button abandons a game.

## Notes / things you may want to extend

- **Dictionary validation**: `word_duel.game_logic.is_valid_word` currently only
  checks length + letters-only. Plug in a word list there if you want to reject
  non-words.
- **Timeouts**: there's no auto-forfeit for an inactive player yet — you'd
  add a `last_action_at` timestamp to the game doc and a periodic job
  (`JobQueue` in python-telegram-bot) to check it.
- **Scaling**: group games are keyed by `chat_id`; inline games are keyed by
  the inline message, so many chats can play at once.
