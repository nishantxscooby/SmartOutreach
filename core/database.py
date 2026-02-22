import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "sent_db.json")


def load_db():
    """Load and return the sent_db.json database as a dictionary."""
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return {}
        return json.loads(content)


def save_db(db):
    """Save the given dictionary back to sent_db.json."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def is_sent(email):
    """Return True if the given email address already exists in the database."""
    db = load_db()
    return email in db


def mark_sent(email, name, sent_time):
    """Add an entry for the given email with replied=false and followup_sent=false."""
    db = load_db()
    db[email] = {
        "name": name,
        "sent_time": sent_time,
        "replied": False,
        "followup_sent": False,
    }
    save_db(db)


def mark_replied(email):
    """Set replied=true for the given email entry."""
    db = load_db()
    if email in db:
        db[email]["replied"] = True
        save_db(db)


def mark_followup_sent(email):
    """Set followup_sent=true for the given email entry."""
    db = load_db()
    if email in db:
        db[email]["followup_sent"] = True
        save_db(db)


def get_all():
    """Return all database entries as a dictionary."""
    return load_db()
