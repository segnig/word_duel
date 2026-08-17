"""
MongoDB data access layer.

Collections:
  games            -- one document per active/finished game, keyed by chat_id
  pending_setup    -- maps a user_id (mid private-message setup) to the game
                       chat_id and role ("A"/"B") they're submitting a secret
                       word for.
"""
from datetime import datetime, timezone

from pymongo import MongoClient

from word_duel.config import MONGO_DB_NAME, MONGO_URI

_client = MongoClient(MONGO_URI)
_db = _client[MONGO_DB_NAME]

games_col = _db["games"]
pending_col = _db["pending_setup"]


def now():
    return datetime.now(timezone.utc)


def create_game(chat_id, word_length, max_rounds):
    game = {
        "_id": chat_id,
        "status": "SETUP",
        "word_length": word_length,
        "max_rounds": max_rounds,
        "players": {},
        "turn": "A",
        "history": [],
        "winner": None,
        "drafts": {"A": "", "B": ""},
        "host_chat_id": chat_id if isinstance(chat_id, int) else None,
        "message_id": None,
        "inline_message_id": None,
        "created_at": now(),
        "updated_at": now(),
    }
    games_col.replace_one({"_id": chat_id}, game, upsert=True)
    return game


def get_game(chat_id):
    return games_col.find_one({"_id": chat_id})


def save_game(game):
    game["updated_at"] = now()
    games_col.replace_one({"_id": game["_id"]}, game, upsert=True)


def delete_game(chat_id):
    games_col.delete_one({"_id": chat_id})


def set_pending(user_id, chat_id, role):
    pending_col.replace_one(
        {"_id": user_id},
        {"_id": user_id, "chat_id": chat_id, "role": role, "created_at": now()},
        upsert=True,
    )


def get_pending(user_id):
    return pending_col.find_one({"_id": user_id})


def clear_pending(user_id):
    pending_col.delete_one({"_id": user_id})
