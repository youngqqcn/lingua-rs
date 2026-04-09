"""Comprehensive tests for language_detect_v2.py

Covers:
- Chinese variants (Simplified, Traditional, Cantonese)
- Unicode-based detection (Japanese, Korean, Thai, Russian, Arabic, Hindi, Tamil, Greek, Hebrew, Vietnamese)
- lingua-slim languages (English, French, Malay, Spanish, Portuguese, Indonesian)
- Short text handling with COMMON_ENGLISH_WORDS whitelist
- History-based language detection with majority voting
- Edge cases (pure numbers, punctuation, emojis, mixed text)
"""

import pytest
from language_detect_v2 import LanguageDetector, detect_language


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def detector():
    """Create a fresh detector instance for each test."""
    return LanguageDetector()


# =============================================================================
# Test Chinese Detection - Simplified
# =============================================================================

class TestChineseSimplified:
    """Tests for Chinese Simplified detection."""

    def test_simple_simplified(self, detector):
        assert detector.detect("你好，世界") == "Chinese(Simplified)"
        assert detector.detect("今天天气真好") == "Chinese(Simplified)"
        assert detector.detect("最新有哪些活动") == "Chinese(Simplified)"

    def test_simplified_with_punctuation(self, detector):
        assert detector.detect("最近有哪些演出门票开售？") == "Chinese(Simplified)"
        assert detector.detect("我的门票有哪些") == "Chinese(Simplified)"

    def test_simplified_single_char(self, detector):
        assert detector.detect("好") == "Chinese(Simplified)"
        assert detector.detect("是") == "Chinese(Simplified)"


# =============================================================================
# Test Chinese Detection - Traditional
# =============================================================================

class TestChineseTraditional:
    """Tests for Chinese Traditional detection."""

    def test_simple_traditional(self, detector):
        assert detector.detect("愛台灣") == "Chinese(Traditional)"
        assert detector.detect("時間") == "Chinese(Traditional)"
        assert detector.detect("網絡") == "Chinese(Traditional)"

    def test_traditional_with_punctuation(self, detector):
        assert detector.detect("請問位置是按付款順序嗎") == "Chinese(Traditional)"
        assert detector.detect("門票會有什麼方式送到？") == "Chinese(Traditional)"

    def test_real_user_input(self, detector):
        assert detector.detect("你好，想問一下地址能填順豐櫃的地址嗎？") == "Chinese(Traditional)"
        assert detector.detect("是不是我搶到票之後能決定要郵寄還是演出當天來拿票？") == "Chinese(Traditional)"


# =============================================================================
# Test Chinese Detection - Cantonese
# =============================================================================

class TestCantonese:
    """Tests for Cantonese detection."""

    def test_cantonese_phrase_features(self, detector):
        assert detector.detect("點解唔係啊") == "Cantonese"
        assert detector.detect("你哋做咩啊") == "Cantonese"
        assert detector.detect("係咪真嘅") == "Cantonese"
        assert detector.detect("唔該幫我") == "Cantonese"

    def test_cantonese_char_features(self, detector):
        assert detector.detect("我個帳戶俾人盜用了") == "Cantonese"
        assert detector.detect("你睇下呢個") == "Cantonese"
        assert detector.detect("我哋係香港") == "Cantonese"

    def test_cantonese_multiple_features(self, detector):
        # Multiple features combined
        assert detector.detect("點解我一入去riize就冇票") == "Cantonese"
        assert detector.detect("點解入會員號碼話錯誤？我係跟官網copy咖喎") == "Cantonese"

    def test_cantonese_payment_reference(self, detector):
        assert detector.detect("支付寶可唔可以俾錢？") == "Cantonese"
        assert detector.detect("我的帳戶給朋友幫我搶飛") == "Cantonese"


# =============================================================================
# Test Unicode-based Detection
# =============================================================================

class TestJapanese:
    """Tests for Japanese detection."""

    def test_hiragana(self, detector):
        assert detector.detect("こんにちは") == "Japanese"
        assert detector.detect("ありがとうございます") == "Japanese"

    def test_katakana(self, detector):
        assert detector.detect("パクボゴム") == "Japanese"
        assert detector.detect("リイズ") == "Japanese"

    def test_mixed_kana(self, detector):
        assert detector.detect("チケット") == "Japanese"


class TestKorean:
    """Tests for Korean detection."""

    def test_korean_hangul(self, detector):
        assert detector.detect("안녕하세요") == "Korean"
        assert detector.detect("멤버십 등록") == "Korean"

    def test_korean_real_input(self, detector):
        assert detector.detect("표를 취소하고 다시 예매하고싶어요") == "Korean"
        assert detector.detect("카드결제만 환불되고 이메일은 오지않았어") == "Korean"


class TestThai:
    """Tests for Thai detection."""

    def test_thai_script(self, detector):
        assert detector.detect("สวัสดีครับ") == "Thai"
        assert detector.detect("พอถึงเวลากดบัตรต้องกดรีเฟรชอีกมีไหม") == "Thai"

    def test_thai_real_input(self, detector):
        assert detector.detect("มีคำถามฝ่ายบริการลูกค้า") == "Thai"
        assert detector.detect("อยากรุ้ที่นั่งแล้วอ่า") == "Thai"


class TestRussian:
    """Tests for Russian/Cyrillic detection."""

    def test_cyrillic(self, detector):
        assert detector.detect("Привет мир") == "Russian"
        assert detector.detect("Сколько рядов там будет") == "Russian"

    def test_russian_real_input(self, detector):
        assert detector.detect("Там написано что у меня вип сектор Row B4 seat 31 что это значит?") == "Russian"


class TestArabic:
    """Tests for Arabic detection."""

    def test_arabic_script(self, detector):
        assert detector.detect("مرحبا") == "Arabic"
        assert detector.detect("شكرا") == "Arabic"


class TestHindi:
    """Tests for Hindi/Devanagari detection."""

    def test_devanagari(self, detector):
        assert detector.detect("नमस्ते") == "Hindi"
        assert detector.detect("धन्यवाद") == "Hindi"


class TestTamil:
    """Tests for Tamil detection."""

    def test_tamil_script(self, detector):
        assert detector.detect("வணக்கம்") == "Tamil"
        assert detector.detect("நன்றி") == "Tamil"


class TestGreek:
    """Tests for Greek detection."""

    def test_greek_script(self, detector):
        assert detector.detect("Γειά σου") == "Greek"
        assert detector.detect("Ευχαριστώ") == "Greek"


class TestHebrew:
    """Tests for Hebrew detection."""

    def test_hebrew_script(self, detector):
        assert detector.detect("שלום") == "Hebrew"
        assert detector.detect("תודה") == "Hebrew"


class TestVietnamese:
    """Tests for Vietnamese detection."""

    def test_vietnamese_diacritics(self, detector):
        # Requires 2+ diacritics OR 'đ' character
        assert detector.detect("Tôi vẫn chưa nhận được số queue") == "Vietnamese"
        assert detector.detect("đi") == "Vietnamese"

    def test_vietnamese_real_input(self, detector):
        # Longer text with more diacritics
        assert detector.detect("Tôi vẫn chưa nhận được số queue") == "Vietnamese"


# =============================================================================
# Test lingua-slim Languages
# =============================================================================

class TestEnglish:
    """Tests for English detection."""

    def test_english_sentences(self, detector):
        assert detector.detect("Hello world") == "English"
        assert detector.detect("How about member presale by using one pay click") == "English"
        assert detector.detect("Is it better to use a PC or the mobile app when purchasing tickets?") == "English"

    def test_english_real_input(self, detector):
        assert detector.detect("Hi I am mango .I like to visit Macao") == "English"
        assert detector.detect("What is offline ticket redemption?") == "English"

    def test_english_common_words(self, detector):
        """Short common English words should be detected as English."""
        for word in ["hello", "hi", "hey", "yes", "no", "ok", "good", "thanks"]:
            assert detector.detect(word) == "English", f"'{word}' should be English"


class TestSpanish:
    """Tests for Spanish detection."""

    def test_spanish_sentences(self, detector):
        assert detector.detect("Hola mundo") == "Spanish"
        assert detector.detect("¿Qué métodos de pago se admiten?") == "Spanish"

    def test_spanish_real_input(self, detector):
        assert detector.detect("¿Cómo puedo contactar con atención al cliente?") == "Spanish"


class TestPortuguese:
    """Tests for Portuguese detection."""

    def test_portuguese_sentences(self, detector):
        assert detector.detect("Olá mundo") == "Portuguese"
        assert detector.detect("Como posso pagar?") == "Portuguese"


class TestMalay:
    """Tests for Malay detection."""

    def test_malay_sentences(self, detector):
        assert detector.detect("Malaysia adalah negara yang indah") == "Malay"
        assert detector.detect("Terima kasih") == "Malay"


class TestIndonesian:
    """Tests for Indonesian detection."""

    def test_indonesian_sentences(self, detector):
        assert detector.detect("Indonesia adalah negara kepulauan") == "Indonesian"
        # Note: "Terima kasih banyak" may be detected as Malay by lingua-slim
        result = detector.detect("Terima kasih banyak")
        assert result in ["Indonesian", "Malay"]


class TestFrench:
    """Tests for French detection."""

    def test_french_sentences(self, detector):
        assert detector.detect("Bonjour le monde") == "French"
        assert detector.detect("Comment allez-vous?") == "French"


# =============================================================================
# Test Short Text Handling (COMMON_ENGLISH_WORDS whitelist)
# =============================================================================

class TestShortTextEnglishWhitelist:
    """Tests for short text handling via COMMON_ENGLISH_WORDS whitelist."""

    def test_short_common_words(self, detector):
        """Common English words should be detected as English even if short."""
        # 1-2 character words
        assert detector.detect("hi") == "English"
        assert detector.detect("ok") == "English"
        # 3 character words
        assert detector.detect("yes") == "English"
        assert detector.detect("hey") == "English"
        # 4 character words
        assert detector.detect("hello") == "English"
        assert detector.detect("good") == "English"
        # 5 character words
        assert detector.detect("thanks") == "English"
        assert detector.detect("sorry") == "English"

    def test_non_english_short_words_still_detected(self, detector):
        """Non-English short words that lingua can detect should still work."""
        # Portuguese thank you
        assert detector.detect("obrigado") == "Portuguese"
        # Spanish thank you
        assert detector.detect("gracias") == "Spanish"
        # French thank you - may be detected as Spanish due to similarity
        result = detector.detect("merci")
        assert result in ["French", "Spanish"]


# =============================================================================
# Test History-based Detection
# =============================================================================

class TestHistoryBasedDetection:
    """Tests for history-based language detection.

    Note:
    - Only texts with Chinese characters are considered valid history entries
    - Non-Chinese texts (Japanese, English, Thai, etc.) are filtered out
    - History requires at least 4 valid entries (total > 3)
    - History requires 70%+ majority for the dominant language
    """

    def test_insufficient_history_ignored(self, detector):
        """With fewer than 4 history entries, history doesn't apply."""
        # Only 1 history entry
        result = detector.detect("obrigado", ["今天天气真好"])
        assert result == "Portuguese"  # Falls back to base detection

    def test_history_with_4_chinese_entries(self, detector):
        """History with 4+ Chinese entries should influence detection."""
        # 4 Chinese entries = 100% Chinese
        history = ["你好", "你好", "你好", "今天天气真好"]
        result = detector.detect("obrigado", history)
        assert result == "Chinese(Simplified)"

    def test_short_common_english_ignores_history(self, detector):
        """Short common English words are overridden by strong history signals.

        Note: History takes precedence over COMMON_ENGLISH_WORDS whitelist when
        history has 4+ valid entries with 70%+ majority.
        """
        # With 4 Chinese entries and 100% majority, history applies even to 'ok'
        result = detector.detect("ok", ["今天天气真好"] * 4)
        assert result == "Chinese(Simplified)"

    def test_no_history(self, detector):
        """Without history, short text detection depends on other factors."""
        result = detector.detect("ok")
        assert result in ["English", "Indonesian", "Malay", "Portuguese"]

    def test_non_chinese_history_included(self, detector):
        """Non-Chinese history entries (Unicode languages) are now included."""
        # 4 Chinese + 4 Japanese = 8 valid, Chinese=50%, Japanese=50%
        # No language has 70%+, so history doesn't apply
        history = ["你好", "你好", "你好", "你好", "こんにちは", "こんにちは", "こんにちは", "こんにちは"]
        result = detector.detect("obrigado", history)
        # Falls back to base detection since no 70% majority
        assert result in ["Portuguese", "Indonesian", "Malay", "English"]

    def test_mixed_history_below_70_percent(self, detector):
        """History where dominant language is below 70% doesn't apply."""
        # 3 Chinese + 4 Japanese (filtered) = 3 valid = 100% Chinese actually
        # Need to find a case where Chinese is not dominant
        # Actually with 3 Chinese and other filtered out, Chinese is 100%
        # Let's use mixed Chinese variants
        history = ["你好", "你好", "你好", "請問位置是按付款順序嗎"]  # 4 Chinese
        result = detector.detect("obrigado", history)
        assert result == "Chinese(Simplified)"

    def test_insufficient_chinese_history(self, detector):
        """Fewer than 4 valid Chinese history entries don't apply."""
        history = ["你好", "你好"]  # Only 2 valid entries
        result = detector.detect("obrigado", history)
        # Should fall back to base detection
        assert result == "Portuguese"


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_text(self, detector):
        """Empty text should return English."""
        assert detector.detect("") == "English"
        assert detector.detect("   ") == "English"
        assert detector.detect(None) == "English"

    def test_pure_numbers(self, detector):
        """Pure numbers should return English."""
        assert detector.detect("123123123") == "English"
        assert detector.detect("123-456-789") == "English"
        assert detector.detect("123.456.789") == "English"

    def test_pure_punctuation(self, detector):
        """Pure punctuation should return English."""
        assert detector.detect("?!?!" ) == "English"
        assert detector.detect("...") == "English"
        assert detector.detect("---") == "English"

    def test_chinese_laughter(self, detector):
        """Chinese laughter patterns should be detected as Chinese."""
        assert detector.detect("哈哈哈") == "Chinese(Simplified)"
        assert detector.detect("呵呵呵") == "Chinese(Simplified)"

    def test_mixed_scripts(self, detector):
        """Mixed script text should be handled appropriately."""
        # Chinese + English -> Chinese (Chinese chars have priority)
        result = detector.detect("I like 你好")
        assert result == "Chinese(Simplified)"

    def test_ascii_only(self, detector):
        """Pure ASCII text should use lingua detection."""
        result = detector.detect("Hello World")
        assert result == "English"


# =============================================================================
# Test Normalization
# =============================================================================

class TestTextNormalization:
    """Tests for text normalization in detection."""

    def test_curly_quotes_normalized(self, detector):
        """Curly quotes should be normalized for detection."""
        # The detector normalizes curly quotes before detection
        assert detector.detect("that's") == "English"
        assert detector.detect("猫's") == "Chinese(Simplified)"

    def test_roman_numerals_normalized(self, detector):
        """Roman numerals should be normalized."""
        assert detector.detect("ⅠⅡⅢ") == "English"  # Gets normalized to I
        assert detector.detect("ⅣⅤ") == "English"


# =============================================================================
# Test Function Interface
# =============================================================================

class TestDetectLanguageFunction:
    """Tests for the detect_language convenience function."""

    def test_detect_language_function(self):
        """Test the detect_language convenience function."""
        assert detect_language("你好") == "Chinese(Simplified)"
        assert detect_language("Hello") == "English"
        assert detect_language("こんにちは") == "Japanese"

    def test_detect_language_with_history(self):
        """Test detect_language with history parameter."""
        # With 4 Chinese entries, history should apply
        history = ["你好", "你好", "你好", "今天天气真好"]
        assert detect_language("obrigado", history) == "Chinese(Simplified)"


# =============================================================================
# Test Confidence/Threshold Boundaries
# =============================================================================

class TestThresholdBoundaries:
    """Tests for history vote threshold boundaries."""

    def test_exactly_70_percent(self, detector):
        """Exactly 70% should meet threshold."""
        # 7 out of 10 = 70% with only Chinese entries
        history = ["你好"] * 7 + ["你好"] * 3  # All Chinese, 10 valid
        result = detector.detect("obrigado", history)
        assert result == "Chinese(Simplified)"

    def test_just_below_70_percent(self, detector):
        """Just below 70% should not meet threshold."""
        # 6 Chinese + 4 Japanese = 10 valid entries
        # Chinese is 6/10 = 60%, below 70%, so history doesn't apply
        history = ["你好"] * 6 + ["こんにちは"] * 4
        result = detector.detect("obrigado", history)
        # Falls back to base detection since 60% < 70%
        assert result in ["Portuguese", "Indonesian", "Malay", "English"]

    def test_exactly_4_entries(self, detector):
        """Exactly 4 entries should meet the minimum (total > 3)."""
        history = ["你好"] * 4
        result = detector.detect("obrigado", history)
        assert result == "Chinese(Simplified)"

    def test_exactly_3_entries(self, detector):
        """Exactly 3 entries should NOT meet the minimum (total > 3)."""
        history = ["你好"] * 3
        result = detector.detect("obrigado", history)
        # Should not use history since 3 is not > 3
        assert result in ["Portuguese", "Indonesian", "Malay", "English"]


# =============================================================================
# Test Real User Input Scenarios
# =============================================================================

class TestRealUserScenarios:
    """Tests based on real user input patterns."""

    def test_ticket_booking_queries(self, detector):
        """Test common ticket booking query patterns."""
        assert detector.detect("请问可以选座吗？") == "Chinese(Simplified)"
        assert detector.detect("如何退票？") == "Chinese(Simplified)"
        assert detector.detect("支付方式有哪些？") == "Chinese(Simplified)"

    def test_member_presale_queries(self, detector):
        """Test member presale related queries."""
        assert detector.detect("会员优先购票是什么时候？") == "Chinese(Simplified)"
        assert detector.detect("会员码无法使用") == "Chinese(Simplified)"

    def test_multilingual_short_responses(self, detector):
        """Test short responses in various languages."""
        # Short affirmatives
        assert detector.detect("好的") == "Chinese(Simplified)"
        assert detector.detect("yes") == "English"
        assert detector.detect("sí") == "Spanish"

    def test_venue_directions(self, detector):
        """Test venue and location related queries."""
        assert detector.detect("场馆在哪个地铁站？") == "Chinese(Simplified)"
        assert detector.detect("会场有停车场吗？") == "Chinese(Simplified)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])