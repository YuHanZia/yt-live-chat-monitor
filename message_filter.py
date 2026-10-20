import re


_YOUTUBE_EMOJI_TOKEN = re.compile(
    r":[a-z0-9]+(?:-[a-z0-9]+)+:",
    re.IGNORECASE,
)
_KEYCAP_SEQUENCE = re.compile(r"[0-9#*]\ufe0f?\u20e3")
_EMOJI_SPECIAL_BASES = {
    0x00A9,
    0x00AE,
    0x203C,
    0x2049,
    0x2122,
    0x2139,
    0x3030,
    0x303D,
    0x3297,
    0x3299,
}


def _is_unicode_emoji_base(char):
    codepoint = ord(char)
    return (
        codepoint in _EMOJI_SPECIAL_BASES
        or 0x1F1E6 <= codepoint <= 0x1F1FF
        or 0x1F300 <= codepoint <= 0x1FAFF
        or 0x2600 <= codepoint <= 0x27BF
    )


def is_emoji_only(text):
    """Return True only when a non-empty message is unambiguously Emoji-only."""
    remaining, youtube_token_count = _YOUTUBE_EMOJI_TOKEN.subn("", text or "")
    remaining, keycap_count = _KEYCAP_SEQUENCE.subn("", remaining)
    saw_emoji = youtube_token_count > 0 or keycap_count > 0

    for char in remaining:
        codepoint = ord(char)
        if char.isspace():
            continue
        if _is_unicode_emoji_base(char):
            saw_emoji = True
            continue
        if codepoint in (0x200D, 0xFE0E, 0xFE0F):
            continue
        if 0x1F3FB <= codepoint <= 0x1F3FF:
            continue
        return False

    return saw_emoji
