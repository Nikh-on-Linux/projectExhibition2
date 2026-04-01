"""
Core text cleaning engine for the emotion analysis pipeline.

Applies all cleaning rules to raw Reddit post text:
- Emoji → descriptive emotion names
- URL / @mention / hashtag removal
- Encoding artifact fixes
- Noise reduction (repeated punctuation, ASCII art, separators)
- Language detection
- Status classification (ok, too_short, non_latin_script, gibberish)

NEVER modifies: negations, contractions, slang, capitalisation, word order.
"""

import re
import unicodedata
from typing import Optional

# ---------------------------------------------------------------------------
# Emoji to descriptive name mapping
# ---------------------------------------------------------------------------
EMOJI_MAP: dict[str, str] = {
    # Angry / frustrated
    "😠": "_angry_face_",
    "😡": "_enraged_face_",
    "😤": "_face_with_steam_",
    "🤬": "_face_with_symbols_on_mouth_",

    # Happy / joy
    "😊": "_smiling_face_",
    "😄": "_grinning_face_",
    "😁": "_beaming_face_",
    "😃": "_grinning_face_with_big_eyes_",
    "🙂": "_slightly_smiling_face_",
    "😀": "_grinning_face_",
    "🥰": "_smiling_face_with_hearts_",
    "😍": "_heart_eyes_face_",

    # Sad
    "😞": "_disappointed_face_",
    "😢": "_crying_face_",
    "😭": "_loudly_crying_face_",
    "😔": "_pensive_face_",
    "🥺": "_pleading_face_",
    "😿": "_crying_cat_",

    # Fear / worry
    "😨": "_fearful_face_",
    "😟": "_worried_face_",
    "😰": "_anxious_face_with_sweat_",
    "😱": "_face_screaming_in_fear_",
    "🫣": "_face_with_peeking_eye_",

    # Surprise
    "😲": "_astonished_face_",
    "😮": "_face_with_open_mouth_",
    "🤯": "_exploding_head_",
    "😯": "_hushed_face_",

    # Disgust
    "🤢": "_nauseated_face_",
    "🤮": "_face_vomiting_",
    "😒": "_unamused_face_",

    # Love / hearts
    "❤️": "_red_heart_",
    "❤": "_red_heart_",
    "💚": "_green_heart_",
    "💙": "_blue_heart_",
    "💛": "_yellow_heart_",
    "💜": "_purple_heart_",
    "🖤": "_black_heart_",
    "🤍": "_white_heart_",
    "💔": "_broken_heart_",
    "💕": "_two_hearts_",
    "💗": "_growing_heart_",
    "💖": "_sparkling_heart_",

    # Misc expressive
    "🔥": "_fire_",
    "🚀": "_rocket_",
    "🎉": "_party_popper_",
    "🌍": "_earth_globe_",
    "✨": "_sparkles_",
    "👍": "_thumbs_up_",
    "👎": "_thumbs_down_",
    "👏": "_clapping_hands_",
    "🙏": "_folded_hands_",
    "💪": "_flexed_biceps_",
    "😂": "_face_with_tears_of_joy_",
    "🤣": "_rolling_on_floor_laughing_",
    "😅": "_grinning_face_with_sweat_",
    "🤔": "_thinking_face_",
    "🤷": "_person_shrugging_",
    "🙄": "_face_with_rolling_eyes_",
    "😴": "_sleeping_face_",
    "🥳": "_partying_face_",
    "😎": "_smiling_face_with_sunglasses_",
    "🤗": "_hugging_face_",
    "😈": "_smiling_face_with_horns_",
    "👀": "_eyes_",
    "💀": "_skull_",
    "🫠": "_melting_face_",
    "💯": "_hundred_points_",
    "⭐": "_star_",
    "🌟": "_glowing_star_",
    "🏆": "_trophy_",
    "⚡": "_high_voltage_",
    "🎯": "_bullseye_",
    "🤝": "_handshake_",
    "✅": "_check_mark_",
    "❌": "_cross_mark_",
    "⚠️": "_warning_",
    "⚠": "_warning_",
    "💡": "_light_bulb_",
    "📢": "_loudspeaker_",
    "🗣️": "_speaking_head_",
    "🗣": "_speaking_head_",
}

# Noise hashtags to strip entirely
NOISE_HASHTAGS = frozenset({
    "ff", "f4f", "l4l", "followme", "follow4follow", "followforfollow",
    "like4like", "likeforlike", "repost", "rt", "tfb", "sfs",
    "followback", "teamfollowback", "instagood", "instadaily",
    "photooftheday", "picoftheday",
})

# Separator / ASCII art patterns
SEPARATOR_RE = re.compile(r"[-=*~_]{4,}")
ASCII_ART_RE = re.compile(r"[|/\\<>^]{3,}")

# URL pattern
URL_RE = re.compile(
    r"https?://\S+|www\.\S+",
    re.IGNORECASE,
)

# @mention pattern
MENTION_RE = re.compile(r"@\w+")

# Hashtag pattern — captures #word
HASHTAG_RE = re.compile(r"#(\w+)")

# Repeated punctuation patterns
REPEATED_EXCLAIM_RE = re.compile(r"!{2,}")
REPEATED_QUESTION_RE = re.compile(r"\?{2,}")
REPEATED_DOT_RE = re.compile(r"\.{4,}")  # 4+ dots → "..."
REPEATED_THREE_DOTS = re.compile(r"\.{2,3}")  # keep "..." or ".." as "..."

# Encoding artifacts
ENCODING_FIXES = {
    "&amp;": "and",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&#39;": "'",
    "&apos;": "'",
    "&nbsp;": " ",
}

# Whitespace collapse
MULTI_SPACE_RE = re.compile(r"[ \t]+")
MULTI_NEWLINE_RE = re.compile(r"\n{2,}")


def _is_latin_script(text: str) -> bool:
    """Check if the majority of alphabetic characters are Latin-based."""
    if not text:
        return True

    latin_count = 0
    non_latin_count = 0

    for ch in text:
        if ch.isalpha():
            try:
                name = unicodedata.name(ch, "")
                if "LATIN" in name:
                    latin_count += 1
                else:
                    non_latin_count += 1
            except ValueError:
                non_latin_count += 1

    total = latin_count + non_latin_count
    if total == 0:
        return True

    return (latin_count / total) > 0.5


def _detect_language(text: str) -> str:
    """
    Detect the language of text. Returns ISO 639-1 code.
    Falls back to 'en' if detection fails or text is too short.
    """
    try:
        from langdetect import detect, LangDetectException
        return detect(text)
    except LangDetectException:
        # Language detection failed (insufficient text, ambiguous, etc.)
        return "en"
    except Exception as e:
        # Unexpected error — log but don't expose
        import logging
        logging.warning(f"Unexpected error in language detection: {e}")
        return "en"


def _is_gibberish(text: str) -> bool:
    """
    Heuristic check for gibberish / spam / bot-generated noise.
    """
    if not text or not text.strip():
        return True

    clean = text.strip()
    # Mostly non-alphabetic characters
    alpha_count = sum(1 for c in clean if c.isalpha())
    if len(clean) > 5 and alpha_count / len(clean) < 0.3:
        return True

    # Random character sequences — very few real words
    words = clean.split()
    if len(words) >= 3:
        # Check if most "words" are very short random strings
        nonsense_words = sum(1 for w in words if len(w) <= 2 and not w.lower() in {
            "i", "a", "an", "am", "is", "it", "in", "on", "at", "to",
            "no", "me", "my", "we", "us", "or", "be", "do", "go", "so",
            "up", "if", "of", "ok",
        })
        if nonsense_words / len(words) > 0.7:
            return True

    return False


def _count_meaningful_words(text: str) -> int:
    """Count meaningful words (length >= 1 alphabetic character)."""
    if not text:
        return 0
    words = text.split()
    return sum(1 for w in words if any(c.isalpha() for c in w))


def _split_camelcase_hashtag(tag: str) -> str:
    """
    Split camelCase or PascalCase hashtag text into space-separated words.
    e.g. 'climateChange' -> 'climate Change', 'ClimateAction' -> 'Climate Action'
    """
    # Insert space before uppercase letters that follow lowercase letters
    result = re.sub(r"([a-z])([A-Z])", r"\1 \2", tag)
    return result


def _replace_emojis(text: str) -> tuple[str, bool]:
    """
    Replace all known emojis with their descriptive names.
    Returns (cleaned_text, had_emojis).
    """
    had_emojis = False
    result = []
    i = 0

    while i < len(text):
        matched = False

        # Try matching multi-char sequences first (e.g. ❤️ is 2 chars)
        for length in (3, 2, 1):
            candidate = text[i:i + length]
            if candidate in EMOJI_MAP:
                result.append(EMOJI_MAP[candidate])
                result.append(" ")  # Add space after emoji for separation
                had_emojis = True
                i += length
                matched = True
                break

        if not matched:
            # Check for any emoji character not in our map — use unicode category
            ch = text[i]
            cat = unicodedata.category(ch)
            # Emoji characters typically fall in 'So' (Symbol, other) category
            # Also check for emoji modifier/component categories
            if cat == "So" or (cat == "Cn" and ord(ch) > 0x1F000):
                # Unknown emoji — use generic placeholder
                try:
                    name = unicodedata.name(ch, "").lower().replace(" ", "_")
                    if name:
                        result.append(f"_{name}_")
                        result.append(" ")  # Add space after emoji for separation
                        had_emojis = True
                    # else skip unknown chars
                except ValueError:
                    pass
                i += 1
            else:
                result.append(ch)
                i += 1

    return "".join(result), had_emojis


def clean_text(raw_text: Optional[str]) -> dict:
    """
    Clean a single raw post text according to all pipeline rules.

    Args:
        raw_text: The original post text to clean.

    Returns:
        dict with keys:
            cleaned_text: str or None
            language: str (ISO 639-1)
            emoji_converted: bool
            status: str (ok, too_short, non_latin_script, gibberish)
            flags: list[str]
    """
    # Handle null / empty input
    if raw_text is None or not raw_text.strip():
        return {
            "cleaned_text": None,
            "language": "en",
            "emoji_converted": False,
            "status": "too_short",
            "flags": [],
        }

    # Normalize unicode to NFC (canonical decomposition) for consistent emoji handling
    text = unicodedata.normalize('NFC', raw_text)
    flags: list[str] = []

    # ── Step 1: Replace emojis ──────────────────────────────────────────
    text, had_emojis = _replace_emojis(text)
    if had_emojis:
        flags.append("had_emojis")

    # ── Step 2: Strip URLs ──────────────────────────────────────────────
    if URL_RE.search(text):
        flags.append("had_urls")
        text = URL_RE.sub("", text)

    # ── Step 3: Strip @mentions ─────────────────────────────────────────
    if MENTION_RE.search(text):
        flags.append("had_mentions")
        text = MENTION_RE.sub("", text)

    # ── Step 4: Process hashtags ────────────────────────────────────────
    hashtag_matches = HASHTAG_RE.findall(text)
    if hashtag_matches:
        flags.append("had_hashtags")

        def _process_hashtag(match: re.Match) -> str:
            tag = match.group(1).lower()
            if tag in NOISE_HASHTAGS:
                return ""  # remove noise hashtags entirely
            # Split camelCase and return the word
            return _split_camelcase_hashtag(match.group(1))

        text = HASHTAG_RE.sub(_process_hashtag, text)

    # ── Step 5: Fix encoding artifacts ──────────────────────────────────
    had_encoding = False
    for entity, replacement in ENCODING_FIXES.items():
        if entity in text:
            text = text.replace(entity, replacement)
            had_encoding = True

    if had_encoding:
        flags.append("encoding_issue")

    # ── Step 6: Remove separator lines and ASCII art ────────────────────
    text = SEPARATOR_RE.sub("", text)
    text = ASCII_ART_RE.sub("", text)

    # ── Step 7: Collapse repeated punctuation ───────────────────────────
    text = REPEATED_EXCLAIM_RE.sub("!", text)
    text = REPEATED_QUESTION_RE.sub("?", text)
    text = REPEATED_DOT_RE.sub("...", text)

    # ── Step 8: Collapse whitespace ─────────────────────────────────────
    text = MULTI_NEWLINE_RE.sub(" ", text)
    text = text.replace("\n", " ")
    text = text.replace("\t", " ")
    text = MULTI_SPACE_RE.sub(" ", text)
    text = text.strip()

    # ── Step 9: Detect language ─────────────────────────────────────────
    # Detect on cleaned text (without emoji placeholders for accuracy)
    text_for_detection = re.sub(r"_\w+_", "", text).strip()
    language = _detect_language(text_for_detection) if text_for_detection else "en"

    # ── Step 10: Check for mixed language ───────────────────────────────
    # Simple heuristic: if langdetect is uncertain, flag as mixed
    try:
        from langdetect import detect_langs
        langs = detect_langs(text_for_detection) if text_for_detection else []
        if len(langs) >= 2 and langs[1].prob > 0.2:
            flags.append("mixed_language")
    except Exception:
        pass

    # ── Step 11: Check all_caps ─────────────────────────────────────────
    alpha_chars = [c for c in text if c.isalpha()]
    if alpha_chars:
        upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        if upper_ratio > 0.7:
            flags.append("all_caps")

    # ── Step 12: Determine status ───────────────────────────────────────
    is_latin = _is_latin_script(text)

    if _count_meaningful_words(text) < 3:
        status = "too_short"
        cleaned_text = None
    elif _is_gibberish(text):
        status = "gibberish"
        cleaned_text = None
    elif not is_latin:
        status = "non_latin_script"
        cleaned_text = text  # clean but flag
    else:
        status = "ok"
        cleaned_text = text

    return {
        "cleaned_text": cleaned_text,
        "language": language,
        "emoji_converted": had_emojis,
        "status": status,
        "flags": flags,
    }


def clean_batch(posts: list[dict]) -> list[dict]:
    """
    Clean an entire batch of posts.

    Args:
        posts: List of dicts with keys: post_id, batch_id, raw_text

    Returns:
        List of dicts with keys:
            post_id, batch_id, cleaned_text, language, emoji_converted, status, flags
    """
    results = []
    for post in posts:
        post_id = post.get("post_id")
        batch_id = post.get("batch_id")
        raw_text = post.get("raw_text")

        cleaned = clean_text(raw_text)
        cleaned["post_id"] = post_id
        cleaned["batch_id"] = batch_id

        results.append(cleaned)

    return results
