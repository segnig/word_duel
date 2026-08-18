# Deploy Word Duel on Render (webhooks)

The bot uses **webhooks** in production (Telegram POSTs to `/telegram`) and
**polling** locally if `WEBHOOK_URL` / `RENDER_EXTERNAL_URL` is not set.

## 1. Atlas

**Network Access** → Allow `0.0.0.0/0` (or Render outbound IPs).

## 2. Push to GitHub

Do **not** commit `.env`.

```bash
git add .
git commit -m "Webhook deploy for Render"
git push origin master
```

## 3. Render web service

1. [render.com](https://render.com) → **New** → **Blueprint** → this repo.
2. `render.yaml` creates a **web** service (not a worker) so it has a public URL.
3. Fill env vars:
   - `BOT_TOKEN`
   - `MONGO_URI` (Atlas connection string)
4. `RENDER_EXTERNAL_URL` is set by Render. The bot registers
   `https://YOUR-APP.onrender.com/telegram` as the Telegram webhook.
5. Wait for deploy. Open `https://YOUR-APP.onrender.com/health` — expect JSON `"status":"ok"`.

## 4. GitHub Action (every 5 minutes)

Keeps the free Render service awake and alerts if `/health` fails.

1. GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. New secret **`HEALTH_URL`** =
   `https://YOUR-APP.onrender.com/health`
3. **Actions** → **Health check** → **Run workflow** once to test.

The workflow file is `.github/workflows/health.yml` (`cron: "*/5 * * * *"`).

## 5. Test the bot

Open your bot in Telegram → `/start`.

## Local run (polling)

```bash
python bot.py
```

No `WEBHOOK_URL` → polling. Telegram must be reachable from your PC.

## Endpoints

| Path | Method | Purpose |
|---|---|---|
| `/health` | GET | Liveness + MongoDB ping |
| `/healthz` | GET | Same as `/health` |
| `/telegram` | POST | Telegram webhook |
| `/` | GET | Simple up check |

Do **not** set `TELEGRAM_PROXY` on Render.
