import json
import os
import sys
import threading
import uuid
from datetime import datetime
from pathlib import Path

APP_DATA_DIR_NAME = "YT直播留言監控"


def get_data_dir():
    if getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA")
        base = (
            Path(local_app_data)
            if local_app_data
            else Path.home() / "AppData" / "Local"
        )
        return base / APP_DATA_DIR_NAME / "data"
    return Path(__file__).resolve().parent / "data"


DATA_DIR = get_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)
WATCHLIST_PATH = DATA_DIR / "watchlist.json"
SETTINGS_PATH = DATA_DIR / "settings.json"

_lock = threading.Lock()

DEFAULT_SETTINGS = {
    "channel_id": "",
    "channel_name": "",
    "discord_webhook_url": "",
    "live_check_interval_sec": 60,
}


def load_watchlist():
    with _lock:
        if not WATCHLIST_PATH.exists():
            return []
        return json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))


def save_watchlist(entries):
    with _lock:
        WATCHLIST_PATH.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def add_watchlist_entry(name, channel_id, note):
    entries = load_watchlist()
    entry = {
        "id": uuid.uuid4().hex[:8],
        "name": name.strip(),
        "channel_id": channel_id.strip(),
        "note": note.strip(),
        "enabled": True,
    }
    entries.append(entry)
    save_watchlist(entries)
    return entry


def update_watchlist_entry(entry_id, fields):
    entries = load_watchlist()
    updated = None
    for e in entries:
        if e["id"] == entry_id:
            e.update(fields)
            updated = e
            break
    save_watchlist(entries)
    return updated


def record_message(entries, channel_id, name):
    """Mutate entries in place for an observed chat message.

    Fills in channel_id for a name-only entry (upgrades precision), or bumps
    last_seen/message_count for a known channel_id, or appends a new
    disabled entry for a never-seen commenter. Returns True if entries changed.
    """
    now = datetime.now().isoformat(timespec="seconds")

    for e in entries:
        if channel_id and e.get("channel_id") == channel_id:
            e["name"] = name
            e["last_seen"] = now
            e["message_count"] = e.get("message_count", 0) + 1
            return True

    for e in entries:
        if not e.get("channel_id") and e.get("name") == name:
            e["channel_id"] = channel_id
            e["last_seen"] = now
            e["message_count"] = e.get("message_count", 0) + 1
            return True

    entries.append({
        "id": uuid.uuid4().hex[:8],
        "name": name,
        "channel_id": channel_id,
        "note": "",
        "enabled": False,
        "last_seen": now,
        "message_count": 1,
    })
    return True


def delete_watchlist_entry(entry_id):
    entries = load_watchlist()
    new_entries = [e for e in entries if e["id"] != entry_id]
    save_watchlist(new_entries)
    return len(new_entries) != len(entries)


def load_settings():
    with _lock:
        if not SETTINGS_PATH.exists():
            return dict(DEFAULT_SETTINGS)
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        merged = dict(DEFAULT_SETTINGS)
        merged.update(data)
        return merged


def save_settings(fields):
    current = load_settings()
    current.update(fields)
    with _lock:
        SETTINGS_PATH.write_text(
            json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return current
