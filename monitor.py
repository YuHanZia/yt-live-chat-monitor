import re
import time
import threading
import traceback
from datetime import datetime

import requests
import pytchat

import storage
from message_filter import is_emoji_only

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9",
}

_status_lock = threading.Lock()
_status = {
    "is_live": False,
    "video_id": None,
    "last_checked": None,
    "last_message_at": None,
    "matched_count": 0,
    "last_error": None,
    "running": False,
}


def get_status():
    with _status_lock:
        return dict(_status)


def _set_status(**kwargs):
    with _status_lock:
        _status.update(kwargs)


def find_live_video_id(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    text = resp.text
    if '"style":"LIVE"' not in text:
        return None
    m = re.search(r'"videoId":"([\w-]{11})"', text)
    return m.group(1) if m else None


def send_discord_alert(webhook_url, entry, author_name, message_text):
    label = entry["name"] or author_name
    embed = {
        "color": 6513407,
        "title": label[:256],
        "description": message_text[:4096],
    }
    try:
        response = requests.post(
            webhook_url,
            json={"embeds": [embed]},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception:
        traceback.print_exc()
        return False


def _match_entry(entries, author_name, author_channel_id):
    for e in entries:
        if not e.get("enabled"):
            continue
        target_id = (e.get("channel_id") or "").strip()
        if target_id:
            if target_id == author_channel_id:
                return e
        else:
            target_name = (e.get("name") or "").strip()
            if target_name and target_name == author_name:
                return e
    return None


def _watch_chat(video_id, stop_event):
    chat = pytchat.create(video_id=video_id, interruptable=False)
    _set_status(is_live=True, video_id=video_id, last_error=None)
    try:
        while chat.is_alive() and not stop_event.is_set():
            items = list(chat.get().sync_items())
            if items:
                settings = storage.load_settings()
                entries = storage.load_watchlist()
                webhook_url = settings.get("discord_webhook_url")
                changed = False
                for c in items:
                    author_name = c.author.name
                    author_channel_id = c.author.channelId
                    matched = _match_entry(entries, author_name, author_channel_id)
                    if matched and webhook_url and not is_emoji_only(c.message):
                        if send_discord_alert(webhook_url, matched, author_name, c.message):
                            with _status_lock:
                                _status["matched_count"] += 1
                    if storage.record_message(entries, author_channel_id, author_name):
                        changed = True
                if changed:
                    storage.save_watchlist(entries)
                _set_status(last_message_at=datetime.now().isoformat(timespec="seconds"))
            time.sleep(2)
    finally:
        try:
            chat.terminate()
        except Exception:
            pass
        _set_status(is_live=False, video_id=None)


def run_forever(stop_event):
    _set_status(running=True)
    while not stop_event.is_set():
        try:
            settings = storage.load_settings()
            channel_id = (settings.get("channel_id") or "").strip()
            interval = int(settings.get("live_check_interval_sec") or 60)
            if not channel_id:
                _set_status(last_error="尚未設定要監控的頻道 channel_id")
                stop_event.wait(interval)
                continue

            video_id = find_live_video_id(channel_id)
            _set_status(last_checked=datetime.now().isoformat(timespec="seconds"))
            if video_id:
                _watch_chat(video_id, stop_event)
            else:
                _set_status(is_live=False, video_id=None)
                stop_event.wait(interval)
        except Exception as exc:
            traceback.print_exc()
            _set_status(last_error=str(exc))
            stop_event.wait(10)
    _set_status(running=False)


def start_background_thread():
    stop_event = threading.Event()
    thread = threading.Thread(target=run_forever, args=(stop_event,), daemon=True)
    thread.start()
    return thread, stop_event
