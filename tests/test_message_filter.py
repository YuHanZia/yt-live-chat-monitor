import unittest

from message_filter import is_emoji_only


class EmojiOnlyTests(unittest.TestCase):
    def test_youtube_emoji_tokens_are_filtered(self):
        self.assertTrue(
            is_emoji_only(
                ":face-green-smiling::face-turquoise-covering-eyes:"
                ":face-turquoise-covering-eyes:"
            )
        )

    def test_unicode_emoji_sequences_are_filtered(self):
        for text in ("😀😀", "👨‍👩‍👧‍👦 👍🏽", "1️⃣"):
            with self.subTest(text=text):
                self.assertTrue(is_emoji_only(text))

    def test_text_mixed_with_emoji_is_not_filtered(self):
        for text in (
            "哈哈 😂",
            "666 🔥",
            "OK 👍",
            "@小白",
            "https://example.com",
            "！！！",
            ":hello:",
        ):
            with self.subTest(text=text):
                self.assertFalse(is_emoji_only(text))

    def test_empty_or_whitespace_message_is_not_filtered(self):
        for text in ("", "   ", "\n"):
            with self.subTest(text=repr(text)):
                self.assertFalse(is_emoji_only(text))


if __name__ == "__main__":
    unittest.main()
