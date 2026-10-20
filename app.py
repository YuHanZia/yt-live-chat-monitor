from flask import Flask, jsonify, request, render_template

import storage
import monitor

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/watchlist", methods=["GET"])
def get_watchlist():
    return jsonify(storage.load_watchlist())


@app.route("/api/watchlist", methods=["POST"])
def create_watchlist_entry():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    channel_id = (data.get("channel_id") or "").strip()
    note = (data.get("note") or "").strip()
    if not name:
        return jsonify({"error": "name 為必填"}), 400
    entry = storage.add_watchlist_entry(name, channel_id, note)
    return jsonify(entry), 201


@app.route("/api/watchlist/<entry_id>", methods=["PATCH"])
def patch_watchlist_entry(entry_id):
    data = request.get_json(force=True) or {}
    allowed = {"name", "channel_id", "note", "enabled"}
    fields = {k: v for k, v in data.items() if k in allowed}
    updated = storage.update_watchlist_entry(entry_id, fields)
    if updated is None:
        return jsonify({"error": "找不到該筆資料"}), 404
    return jsonify(updated)


@app.route("/api/watchlist/<entry_id>", methods=["DELETE"])
def delete_watchlist_entry(entry_id):
    ok = storage.delete_watchlist_entry(entry_id)
    if not ok:
        return jsonify({"error": "找不到該筆資料"}), 404
    return jsonify({"deleted": True})


@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify(storage.load_settings())


@app.route("/api/settings", methods=["POST"])
def post_settings():
    data = request.get_json(force=True) or {}
    allowed = {"channel_id", "channel_name", "discord_webhook_url", "live_check_interval_sec"}
    fields = {k: v for k, v in data.items() if k in allowed}
    settings = storage.save_settings(fields)
    return jsonify(settings)


@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify(monitor.get_status())


@app.route("/api/test-webhook", methods=["POST"])
def test_webhook():
    settings = storage.load_settings()
    webhook_url = settings.get("discord_webhook_url")
    if not webhook_url:
        return jsonify({"error": "尚未設定 Discord Webhook 網址"}), 400
    import requests
    try:
        r = requests.post(webhook_url, json={"content": "✅ 測試通知：YT 留言監控已連接成功"}, timeout=10)
        r.raise_for_status()
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"ok": True})


if __name__ == "__main__":
    monitor.start_background_thread()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
