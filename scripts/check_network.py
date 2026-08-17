#!/usr/bin/env python3
"""Quick check: can this machine reach Telegram and MongoDB?"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def check(name, fn):
    try:
        fn()
        print(f"  OK  {name}")
        return True
    except Exception as exc:
        print(f"  FAIL {name}: {exc}")
        return False


def main():
    print("Network check\n")

    import urllib.request

    def telegram():
        urllib.request.urlopen("https://api.telegram.org", timeout=15)

    def internet():
        urllib.request.urlopen("https://google.com", timeout=15)

    ok_tg = check("Telegram (api.telegram.org)", telegram)
    check("Internet (google.com)", internet)

    uri = os.environ.get("MONGO_URI") or os.environ.get("MONGODB_URI", "")
    if uri:
        def mongo():
            from word_duel.db import check_connection
            check_connection()
        check("MongoDB Atlas", mongo)
    else:
        print("  SKIP MongoDB (no MONGO_URI in .env)")

    print()
    if not ok_tg:
        print("Telegram is blocked on this network.")
        print("Fix: use VPN, TELEGRAM_PROXY in .env, or deploy to Render/Railway.")
        print("See docs/DEPLOY.md")
        sys.exit(1)
    print("All checks passed — run: python bot.py")


if __name__ == "__main__":
    main()
