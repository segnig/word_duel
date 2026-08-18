"""HTTP health payload used by Render and GitHub Actions."""

from datetime import datetime, timezone

from word_duel import db
from word_duel.config import WEBHOOK_URL


def health_payload():
    mongo = "ok"
    try:
        db.ping()
    except Exception:
        mongo = "error"

    status = "ok" if mongo == "ok" else "degraded"
    return status, {
        "status": status,
        "service": "word-duel",
        "mongodb": mongo,
        "mode": "webhook" if WEBHOOK_URL else "polling",
        "time": datetime.now(timezone.utc).isoformat(),
    }
