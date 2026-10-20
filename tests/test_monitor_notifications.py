import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import monitor


class _FakeChat:
    def __init__(self, items):
        self._items = items

    def is_alive(self):
        return True

    def get(self):
        return SimpleNamespace(sync_items=lambda: iter(self._items))

    def terminate(self):
        return None


class DiscordNotificationTests(unittest.TestCase):
    @patch("monitor.requests.post")
    def test_notification_uses_minimal_embed(self, post):
        post.return_value = Mock()

        sent = monitor.send_discord_alert(
            "https://example.invalid",
            {"name": "小白"},
            "@小白",
            "你好",
        )

        self.assertIs(sent, True)
        self.assertEqual(
            post.call_args.kwargs["json"],
            {
                "embeds": [
                    {
                        "color": 6513407,
                        "title": "小白",
                        "description": "你好",
                    }
                ]
            },
        )

    @patch("monitor.requests.post")
    def test_notification_respects_discord_embed_limits(self, post):
        post.return_value = Mock()

        sent = monitor.send_discord_alert(
            "https://example.invalid",
            {"name": "人" * 300},
            "@備用名稱",
            "留言" * 2500,
        )

        self.assertIs(sent, True)
        embed = post.call_args.kwargs["json"]["embeds"][0]
        self.assertEqual(len(embed["title"]), 256)
        self.assertEqual(len(embed["description"]), 4096)

    @patch("monitor.requests.post")
    def test_http_failure_returns_false(self, post):
        post.return_value.raise_for_status.side_effect = RuntimeError("failed")

        with patch("monitor.traceback.print_exc"):
            sent = monitor.send_discord_alert(
                "https://example.invalid",
                {"name": "小白"},
                "@小白",
                "你好",
            )

        self.assertIs(sent, False)

    @patch("monitor.send_discord_alert")
    @patch("monitor.storage.save_watchlist")
    @patch("monitor.storage.load_watchlist")
    @patch("monitor.storage.load_settings")
    @patch("monitor.pytchat.create")
    def test_emoji_only_message_updates_stats_without_sending(
        self,
        create_chat,
        load_settings,
        load_watchlist,
        save_watchlist,
        send_alert,
    ):
        entries = [
            {
                "id": "tracked",
                "name": "小白",
                "channel_id": "UC_TRACKED",
                "enabled": True,
                "message_count": 0,
            }
        ]
        message = SimpleNamespace(
            author=SimpleNamespace(name="@小白", channelId="UC_TRACKED"),
            message=":face-green-smiling::face-turquoise-covering-eyes:",
        )
        create_chat.return_value = _FakeChat([message])
        load_settings.return_value = {"discord_webhook_url": "https://example.invalid"}
        load_watchlist.return_value = entries
        stop_event = threading.Event()

        with patch("monitor.time.sleep", side_effect=lambda _seconds: stop_event.set()):
            monitor._watch_chat("61uAGCzJPSQ", stop_event)

        send_alert.assert_not_called()
        self.assertEqual(entries[0]["message_count"], 1)
        save_watchlist.assert_called_once_with(entries)


if __name__ == "__main__":
    unittest.main()
