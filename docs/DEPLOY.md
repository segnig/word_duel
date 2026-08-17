# Deploy Word Duel (when Telegram is blocked locally)

If `python bot.py` shows **MongoDB connected** but **Telegram timed out**,
your PC cannot reach `api.telegram.org`. Deploy the bot to the cloud instead.
You still use the bot normally in Telegram on your phone.

## Option A — Render (free, recommended)

1. Push this project to **GitHub** (do not commit `.env`).
2. Go to [render.com](https://render.com) → sign up → **New** → **Blueprint**.
3. Connect your GitHub repo. Render reads `render.yaml`.
4. Add **Environment Variables** in the Render dashboard:
   - `BOT_TOKEN` — from BotFather
   - `MONGO_URI` or `MONGODB_URI` — your Atlas connection string
   - `MONGO_DB_NAME` — `word_duel`
5. Click **Deploy**. The **Worker** service runs `python bot.py` 24/7.
6. Open your bot in Telegram and test `/start`.

Atlas **Network Access** must allow Render’s IPs, or use `0.0.0.0/0` (allow all).

## Option B — VPN on your PC

1. Connect a VPN that allows Telegram.
2. Run:
   ```bash
   python scripts/check_network.py
   python bot.py
   ```

## Option C — Local SOCKS proxy

If your VPN app exposes SOCKS5 on localhost:

```env
TELEGRAM_PROXY=socks5://127.0.0.1:1080
```

Install SOCKS support:
```bash
pip install "python-telegram-bot[socks]"
```

Then run `python bot.py`.

## Option D — Docker (any VPS)

On a server where Telegram works (DigitalOcean, AWS, etc.):

```bash
docker build -t word-duel .
docker run -d --env-file .env --name word-duel word-duel
```

Use the same `.env` variables as locally (never commit `.env`).
