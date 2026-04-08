#!/usr/bin/env python3
"""
Language detection v2 - uses Unicode detection for non-latin languages
and lingua-slim (English, Malay, Spanish, Portuguese, Indonesian)
for latin-based language detection.

Install: pip install lingua-slim
"""

import re

from lingua import Language, LanguageDetectorBuilder


class LanguageDetector:
    """
    Language detector combining Unicode-based detection for CJK/Thai/Cyrillic/etc.
    and lingua-slim for Latin-based language detection.

    Supported languages:
    - Unicode-based: Chinese, Japanese, Korean, Thai, Russian, Arabic,
      Hindi, Tamil, Greek, Hebrew, Vietnamese
    - lingua-slim: English, Malay, Spanish, Portuguese, Indonesian
    """

    # Unicode ranges for various languages/scripts
    UNICODE_RANGES = {
        "Chinese": r'[\u4e00-\u9fff\u3400-\u4dbf]',
        "Japanese": r'[\u3040-\u309f\u30a0-\u30ff]',
        "Korean": r'[\uac00-\ud7af\u1100-\u11ff]',
        "Thai": r'[\u0e00-\u0e7f]',
        "Cyrillic": r'[\u0400-\u04ff]',
        "Vietnamese": r'[ăâăắầằẩấđêĩôơưạảấầẩằắặậẽẻẹếềểễệỉịỏọốồổộớờởợụủứừửựỹỵỷ]',
        "Arabic": r'[\u0600-\u06ff\u0750-\u077f]',
        "Devanagari": r'[\u0900-\u097f]',
        "Tamil": r'[\u0b80-\u0bff]',
        "Hebrew": r'[\u0590-\u05ff]',
        "Greek": r'[\u0370-\u03ff]',
    }

    # Map lingua Language enum to display names
    LINGUA_LANG_MAP = {
        Language.ENGLISH: "English",
        Language.MALAY: "Malay",
        Language.SPANISH: "Spanish",
        Language.PORTUGUESE: "Portuguese",
        Language.INDONESIAN: "Indonesian",
    }

    # Strong languages that can help determine short text language
    STRONG_LANGUAGES = {
        "Chinese", "Japanese", "Korean", "Thai", "Russian",
        "Arabic", "Hindi", "Tamil", "Greek", "Hebrew", "Vietnamese"
    }

    def __init__(self):
        """Initialize the detector."""
        self._detector = None

    def _is_long_text(self, text: str) -> bool:
        """Check if text is long enough to be used for history."""
        stripped = text.strip()
        if stripped.isascii():
            # English: >= 5 words
            word_count = len(stripped.split())
            return word_count >= 5
        elif any("\u4e00" <= c <= "\u9fff" for c in stripped):
            # Chinese: >= 5 characters
            chinese_count = sum(1 for c in stripped if "\u4e00" <= c <= "\u9fff")
            return chinese_count >= 5
        else:
            # Other: >= 5 characters
            return len(stripped) >= 5

    def _detect_by_unicode(self, text: str) -> str | None:
        """Detect language by Unicode character ranges."""
        if not text or not text.strip():
            return None

        if re.search(self.UNICODE_RANGES["Chinese"], text):
            return "Chinese"
        if re.search(self.UNICODE_RANGES["Japanese"], text):
            return "Japanese"
        if re.search(self.UNICODE_RANGES["Korean"], text):
            return "Korean"
        if re.search(self.UNICODE_RANGES["Thai"], text):
            return "Thai"
        if re.search(self.UNICODE_RANGES["Cyrillic"], text):
            return "Russian"
        if re.search(self.UNICODE_RANGES["Arabic"], text):
            return "Arabic"
        if re.search(self.UNICODE_RANGES["Devanagari"], text):
            return "Hindi"
        if re.search(self.UNICODE_RANGES["Tamil"], text):
            return "Tamil"
        if re.search(self.UNICODE_RANGES["Greek"], text):
            return "Greek"
        if re.search(self.UNICODE_RANGES["Hebrew"], text):
            return "Hebrew"

        return None

    def _build_lingua_detector(self):
        """Build lingua detector with 5 languages."""
        return LanguageDetectorBuilder.from_languages(
            Language.ENGLISH,
            Language.MALAY,
            Language.SPANISH,
            Language.PORTUGUESE,
            Language.INDONESIAN,
        ).build()

    def _get_lingua_detector(self):
        """Get singleton lingua detector."""
        if self._detector is None:
            self._detector = self._build_lingua_detector()
        return self._detector

    def _detect_base(self, text: str) -> str:
        """Base detection without history."""
        if not text or not text.strip():
            return "English"

        text = text.strip()

        # First try Unicode-based detection for non-latin languages
        unicode_lang = self._detect_by_unicode(text)
        if unicode_lang:
            return unicode_lang

        # Then try lingua for latin-based languages
        try:
            detector = self._get_lingua_detector()
            result = detector.detect_language_of(text)
            if result:
                return self.LINGUA_LANG_MAP.get(result, "English")
        except Exception:
            pass

        # Default to English for ASCII-only text
        return "English"

    def detect(self, text: str, history: list[str] | None = None) -> str:
        """
        Detect language of the given text.

        Args:
            text: Input text to detect language for.
            history: Optional list of previous texts to help determine
                    language for short ambiguous texts.

        Returns:
            Language name as string (e.g., "Chinese", "English", "Spanish").
            Defaults to "English" for unknown/ASCII text.
        """
        if not text or not text.strip():
            return "English"

        stripped = text.strip()

        # Check if text is pure number (may be phone, date, etc.)
        is_pure_number = bool(
            re.match(r'^[\d\-\.\s\(\)]+$', stripped) and
            stripped.replace('-', '').replace('.', '').replace(' ', '').replace('(', '').replace(')', '').isdigit()
        )

        result = self._detect_base(text)

        # If text is long and a strong language, return directly
        if self._is_long_text(text) and result in self.STRONG_LANGUAGES:
            return result

        # If text is short (or pure number) and has history, use history
        if (not self._is_long_text(text) or is_pure_number) and history:
            for hist_text in history:
                if self._is_long_text(hist_text):
                    hist_result = self._detect_base(hist_text)
                    if hist_result in self.STRONG_LANGUAGES:
                        return hist_result

        return result


# Singleton instance for convenience
_detector = None


def detect_language(text: str, history: list[str] | None = None) -> str:
    """
    Detect language of the given text (convenience function).

    Args:
        text: Input text to detect language for.
        history: Optional list of previous texts to help determine
                language for short ambiguous texts.

    Returns:
        Language name as string.
    """
    global _detector
    if _detector is None:
        _detector = LanguageDetector()
    return _detector.detect(text, history)


if __name__ == "__main__":
    # Test
    detector = LanguageDetector()

    tests = [
        "你好，世界",
        "こんにちは",
        "안녕하세요",
        "สวัสดีครับ",
        "Привет мир",
        "مرحبا",
        "नमस्ते",
        "வணக்கம்",
        "Hola mundo",
        "Olá mundo",
        "Bonjour monde",
        "Hello world",
        "Malaysia adalah negara yang indah",
        "Indonesia adalah negara kepulauan",
    ]

    print("=== Class-based detection ===")
    for t in tests:
        print(f"{t[:30]:30} -> {detector.detect(t)}")

    print("\n=== Function-based detection ===")
    for t in tests:
        print(f"{t[:30]:30} -> {detect_language(t)}")

    # Test with history
    print("\n=== Test with history (short 'ok' after Chinese) ===")
    history = ["今天天气真好"]
    print(f"'ok' with history={history} -> {detect_language('ok', history)}")

    print(f"'ok' without history -> {detect_language('ok')}")
