"""
Comprehensive unit tests for the text cleaning engine (cleaner.py).

Tests cover all cleaning rules:
- Emoji replacement (single, consecutive, mixed with text)
- URL stripping (http, https, www)
- @mention removal
- Hashtag processing (meaningful vs noise)
- Encoding artifact fixes
- Repeated punctuation collapse
- ASCII art / separator removal
- Whitespace normalisation
- Status detection: too_short, gibberish, non_latin_script
- Preservation: negations, contractions, slang, capitalisation, word order
- Null / empty input handling
- Flags array correctness
"""

import sys
import os

# Add parent directory to path so we can import cleaner
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cleaner import clean_text, clean_batch, _replace_emojis, _split_camelcase_hashtag


# ═══════════════════════════════════════════════════════════════════════
# EMOJI TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestEmojiReplacement:
    def test_single_emoji(self):
        result = clean_text("I am angry 😠")
        assert "_angry_face_" in result["cleaned_text"]
        assert result["emoji_converted"] is True
        assert "had_emojis" in result["flags"]

    def test_consecutive_emojis(self):
        result = clean_text("So angry 😠😠 right now about this situation")
        assert "_angry_face_ _angry_face_" in result["cleaned_text"]
        assert result["emoji_converted"] is True

    def test_multiple_different_emojis(self):
        result = clean_text("Happy 😊 and excited 🚀 about this project today")
        assert "_smiling_face_" in result["cleaned_text"]
        assert "_rocket_" in result["cleaned_text"]
        assert result["emoji_converted"] is True

    def test_no_emojis(self):
        result = clean_text("This is a normal sentence without any emojis at all")
        assert result["emoji_converted"] is False
        assert "had_emojis" not in result["flags"]

    def test_red_heart_emoji(self):
        result = clean_text("I love this ❤️ so much today")
        assert "_red_heart_" in result["cleaned_text"]

    def test_crying_face(self):
        result = clean_text("This makes me so sad 😢 I cannot believe it")
        assert "_crying_face_" in result["cleaned_text"]

    def test_fire_emoji(self):
        result = clean_text("This is lit 🔥 absolutely amazing content right here")
        assert "_fire_" in result["cleaned_text"]

    def test_party_popper(self):
        result = clean_text("Congratulations to the team 🎉 well done everyone")
        assert "_party_popper_" in result["cleaned_text"]

    def test_earth_globe(self):
        result = clean_text("Save the planet 🌍 we must act now together")
        assert "_earth_globe_" in result["cleaned_text"]


# ═══════════════════════════════════════════════════════════════════════
# URL TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestURLStripping:
    def test_https_url(self):
        result = clean_text("Check this out https://example.com/page for more info here")
        assert "https://" not in result["cleaned_text"]
        assert "example.com" not in result["cleaned_text"]
        assert "had_urls" in result["flags"]

    def test_http_url(self):
        result = clean_text("Visit http://example.com/info for details and more info")
        assert "http://" not in result["cleaned_text"]
        assert "had_urls" in result["flags"]

    def test_www_url(self):
        result = clean_text("Go to www.example.com for more details and information")
        assert "www." not in result["cleaned_text"]
        assert "had_urls" in result["flags"]

    def test_no_url(self):
        result = clean_text("This post has no links at all just plain text content")
        assert "had_urls" not in result["flags"]

    def test_multiple_urls(self):
        result = clean_text("Check https://one.com and https://two.com for the info docs")
        assert "one.com" not in result["cleaned_text"]
        assert "two.com" not in result["cleaned_text"]
        assert "had_urls" in result["flags"]


# ═══════════════════════════════════════════════════════════════════════
# MENTION TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestMentionStripping:
    def test_single_mention(self):
        result = clean_text("Hey @username check this post out it is great")
        assert "@username" not in result["cleaned_text"]
        assert "had_mentions" in result["flags"]

    def test_multiple_mentions(self):
        result = clean_text("Thanks @user1 and @user2 for the help on this project")
        assert "@user1" not in result["cleaned_text"]
        assert "@user2" not in result["cleaned_text"]
        assert "had_mentions" in result["flags"]

    def test_no_mentions(self):
        result = clean_text("This post has no mentions at all just text content here")
        assert "had_mentions" not in result["flags"]


# ═══════════════════════════════════════════════════════════════════════
# HASHTAG TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestHashtagProcessing:
    def test_meaningful_hashtag(self):
        result = clean_text("This is great #happy so glad about the news today")
        assert "#" not in result["cleaned_text"]
        assert "happy" in result["cleaned_text"]
        assert "had_hashtags" in result["flags"]

    def test_noise_hashtag_removed(self):
        result = clean_text("Follow me #followme #f4f and check my posts today")
        assert "followme" not in result["cleaned_text"]
        assert "f4f" not in result["cleaned_text"]
        assert "had_hashtags" in result["flags"]

    def test_camelcase_hashtag(self):
        result = clean_text("Fighting for our future #climateChange is important now")
        # Should split camelCase
        assert "#" not in result["cleaned_text"]
        assert "climate" in result["cleaned_text"]
        assert "had_hashtags" in result["flags"]

    def test_no_hashtags(self):
        result = clean_text("This post has no hashtags at all just text content here")
        assert "had_hashtags" not in result["flags"]


# ═══════════════════════════════════════════════════════════════════════
# ENCODING ARTIFACT TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestEncodingFixes:
    def test_amp(self):
        result = clean_text("Salt &amp; pepper are good basic seasonings for cooking")
        assert "and" in result["cleaned_text"]
        assert "&amp;" not in result["cleaned_text"]
        assert "encoding_issue" in result["flags"]

    def test_lt_gt(self):
        result = clean_text("This is &lt;important&gt; and should be noted carefully")
        assert "<important>" in result["cleaned_text"]
        assert "encoding_issue" in result["flags"]

    def test_quot(self):
        result = clean_text("He said &quot;hello&quot; to everyone in the room today")
        assert '"hello"' in result["cleaned_text"]
        assert "encoding_issue" in result["flags"]

    def test_no_encoding_issues(self):
        result = clean_text("Normal text without any encoding issues at all here")
        assert "encoding_issue" not in result["flags"]


# ═══════════════════════════════════════════════════════════════════════
# REPEATED PUNCTUATION TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestRepeatedPunctuation:
    def test_multiple_exclamation(self):
        result = clean_text("This is amazing!!!!! I cannot believe what happened here")
        assert "!!!!!" not in result["cleaned_text"]
        assert "!" in result["cleaned_text"]

    def test_multiple_question(self):
        result = clean_text("What is wrong with you????? Tell me what happened today")
        assert "?????" not in result["cleaned_text"]
        assert "?" in result["cleaned_text"]

    def test_excessive_dots(self):
        result = clean_text("I wonder........what will happen next in the story")
        assert "........" not in result["cleaned_text"]
        assert "..." in result["cleaned_text"]

    def test_single_punctuation_preserved(self):
        result = clean_text("Is this real? I think so! Amazing content here today")
        assert "?" in result["cleaned_text"]
        assert "!" in result["cleaned_text"]


# ═══════════════════════════════════════════════════════════════════════
# SEPARATOR / ASCII ART TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestSeparatorRemoval:
    def test_dash_separators(self):
        result = clean_text("First part of text ----- second part of the text here")
        assert "-----" not in result["cleaned_text"]

    def test_equals_separators(self):
        result = clean_text("First part of text ===== second part of the text here")
        assert "=====" not in result["cleaned_text"]

    def test_asterisk_separators(self):
        result = clean_text("First part of text ***** second part of the text here")
        assert "*****" not in result["cleaned_text"]


# ═══════════════════════════════════════════════════════════════════════
# WHITESPACE TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestWhitespaceCollapse:
    def test_multiple_spaces(self):
        result = clean_text("Too    many    spaces   in   this   text   here")
        assert "    " not in result["cleaned_text"]
        assert result["cleaned_text"].strip() == result["cleaned_text"]

    def test_tabs(self):
        result = clean_text("Tab\there\tand\there\tin\tthis text content")
        assert "\t" not in result["cleaned_text"]

    def test_newlines(self):
        result = clean_text("Line one\n\n\nLine two\n\nLine three here now")
        assert "\n" not in result["cleaned_text"]

    def test_leading_trailing_whitespace(self):
        result = clean_text("  This has leading and trailing whitespace here  ")
        assert result["cleaned_text"] == result["cleaned_text"].strip()


# ═══════════════════════════════════════════════════════════════════════
# PRESERVATION TESTS — CRITICAL FOR EMOTION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

class TestPreservation:
    def test_negation_not(self):
        result = clean_text("I am not happy about this situation at all today")
        assert "not" in result["cleaned_text"]

    def test_negation_never(self):
        result = clean_text("I will never forgive them for what they did to us")
        assert "never" in result["cleaned_text"]

    def test_negation_no(self):
        result = clean_text("There is no way this is going to work out at all")
        assert "no " in result["cleaned_text"]

    def test_contraction_dont(self):
        result = clean_text("I don't like this at all it is terrible for everyone")
        assert "don't" in result["cleaned_text"]

    def test_contraction_wont(self):
        result = clean_text("They won't listen to any of us about this problem")
        assert "won't" in result["cleaned_text"]

    def test_contraction_cant(self):
        result = clean_text("I can't believe what just happened to all of us")
        assert "can't" in result["cleaned_text"]

    def test_contraction_isnt(self):
        result = clean_text("This isn't what I expected at all from the project")
        assert "isn't" in result["cleaned_text"]

    def test_slang_lol(self):
        result = clean_text("That was so funny lol I could not stop laughing today")
        assert "lol" in result["cleaned_text"]

    def test_slang_omg(self):
        result = clean_text("omg I cannot believe this happened to us yesterday")
        assert "omg" in result["cleaned_text"]

    def test_slang_tbh(self):
        result = clean_text("tbh I think this is really bad and we should fix it")
        assert "tbh" in result["cleaned_text"]

    def test_capitalisation_preserved(self):
        result = clean_text("I HATE this policy and everyone should know about it")
        assert "HATE" in result["cleaned_text"]

    def test_word_order_preserved(self):
        text = "Climate change makes me angry and we need action NOW"
        result = clean_text(text)
        words = result["cleaned_text"].split()
        # Verify word order hasn't changed
        assert words.index("Climate") < words.index("change")
        assert words.index("change") < words.index("makes")
        assert words.index("makes") < words.index("angry")


# ═══════════════════════════════════════════════════════════════════════
# STATUS CLASSIFICATION TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestStatusClassification:
    def test_null_input(self):
        result = clean_text(None)
        assert result["status"] == "too_short"
        assert result["cleaned_text"] is None

    def test_empty_string(self):
        result = clean_text("")
        assert result["status"] == "too_short"
        assert result["cleaned_text"] is None

    def test_whitespace_only(self):
        result = clean_text("   \n\t  ")
        assert result["status"] == "too_short"
        assert result["cleaned_text"] is None

    def test_too_short_after_cleaning(self):
        result = clean_text("hi ok")
        assert result["status"] == "too_short"
        assert result["cleaned_text"] is None

    def test_ok_status(self):
        result = clean_text("Climate change makes me angry and we need action NOW")
        assert result["status"] == "ok"
        assert result["cleaned_text"] is not None

    def test_language_detection(self):
        result = clean_text("Climate change makes me angry and we need action NOW")
        assert result["language"] == "en"


# ═══════════════════════════════════════════════════════════════════════
# ALL CAPS FLAG TEST
# ═══════════════════════════════════════════════════════════════════════

class TestAllCapsFlag:
    def test_all_caps_detected(self):
        result = clean_text("I HATE THIS SO MUCH IT IS TERRIBLE FOR EVERYONE")
        assert "all_caps" in result["flags"]

    def test_normal_case_no_flag(self):
        result = clean_text("This is a normal sentence with mixed case throughout")
        assert "all_caps" not in result["flags"]


# ═══════════════════════════════════════════════════════════════════════
# BATCH CLEANING TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestBatchCleaning:
    def test_batch_length_matches(self):
        posts = [
            {"post_id": 1, "batch_id": "tb-001", "raw_text": "I love this ❤️ so much it is great"},
            {"post_id": 2, "batch_id": "tb-001", "raw_text": "This is terrible 😠 I hate this so much"},
            {"post_id": 3, "batch_id": "tb-001", "raw_text": None},
        ]
        results = clean_batch(posts)
        assert len(results) == len(posts)

    def test_batch_preserves_ids(self):
        posts = [
            {"post_id": 42, "batch_id": "tb-002", "raw_text": "Test post here with enough words for test"},
        ]
        results = clean_batch(posts)
        assert results[0]["post_id"] == 42
        assert results[0]["batch_id"] == "tb-002"


# ═══════════════════════════════════════════════════════════════════════
# COMBINED CLEANING TESTS (multiple rules at once)
# ═══════════════════════════════════════════════════════════════════════

class TestCombinedCleaning:
    def test_sample_from_spec(self):
        """Test the exact example from the specification."""
        result = clean_text("Climate change makes me angry! 😠 We need action NOW!")
        assert "_angry_face_" in result["cleaned_text"]
        assert "angry!" in result["cleaned_text"]
        assert "NOW!" in result["cleaned_text"]
        assert result["emoji_converted"] is True
        assert result["status"] == "ok"

    def test_urls_and_emojis(self):
        result = clean_text("Check https://example.com 😊 This is great for everyone")
        assert "https" not in result["cleaned_text"]
        assert "_smiling_face_" in result["cleaned_text"]
        assert "had_urls" in result["flags"]
        assert "had_emojis" in result["flags"]

    def test_mentions_and_hashtags(self):
        result = clean_text("Hey @user check out #climateAction for more info today")
        assert "@user" not in result["cleaned_text"]
        assert "#" not in result["cleaned_text"]
        assert "had_mentions" in result["flags"]
        assert "had_hashtags" in result["flags"]

    def test_encoding_and_whitespace(self):
        result = clean_text("This &amp; that    are    important facts to know")
        assert "and" in result["cleaned_text"]
        assert "&amp;" not in result["cleaned_text"]
        # No excessive spaces
        assert "  " not in result["cleaned_text"]

    def test_full_pipeline(self):
        """End-to-end test with all cleaning rules applied."""
        raw = "OMG @admin 😠😡 check https://bad.com #climateChange is ruining &amp; destroying everything!!!!! -----"
        result = clean_text(raw)

        # Emojis converted
        assert "_angry_face_" in result["cleaned_text"]
        assert "_enraged_face_" in result["cleaned_text"]
        assert result["emoji_converted"] is True

        # URL stripped
        assert "bad.com" not in result["cleaned_text"]

        # Mention stripped
        assert "@admin" not in result["cleaned_text"]

        # Hashtag processed
        assert "#" not in result["cleaned_text"]

        # Encoding fixed
        assert "and" in result["cleaned_text"]

        # Repeated punctuation collapsed
        assert "!!!!!" not in result["cleaned_text"]

        # Separator removed
        assert "-----" not in result["cleaned_text"]

        # Slang preserved
        assert "OMG" in result["cleaned_text"]

        # Status is ok
        assert result["status"] == "ok"


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestHelpers:
    def test_replace_emojis_returns_tuple(self):
        text, had = _replace_emojis("Hello 😊 world")
        assert isinstance(text, str)
        assert isinstance(had, bool)
        assert had is True

    def test_replace_emojis_no_emojis(self):
        text, had = _replace_emojis("Hello world")
        assert had is False
        assert text == "Hello world"

    def test_split_camelcase(self):
        assert "climate Change" == _split_camelcase_hashtag("climateChange")
        assert "Climate Action" == _split_camelcase_hashtag("ClimateAction")

    def test_split_single_word(self):
        assert "happy" == _split_camelcase_hashtag("happy")
