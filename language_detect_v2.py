#!/usr/bin/env python3
"""
Language detection v2 - uses Unicode detection for non-latin languages
and lingua-slim (English, Malay, Spanish, Portuguese, Indonesian)
for latin-based language detection.

Install: pip install lingua-slim
"""

import re
from functools import lru_cache
from lingua import Language, LanguageDetectorBuilder

# Unicode ranges for various languages/scripts
UNICODE_RANGES = {
    # CJK: Chinese, Japanese, Korean
    "chinese": r'[\u4e00-\u9fff\u3400-\u4dbf]',  # Chinese characters
    "japanese": r'[\u3040-\u309f\u30a0-\u30ff]',  # Hiragana & Katakana
    "korean": r'[\uac00-\ud7af\u1100-\u11ff]',  # Korean Hangul
    # Thai
    "thai": r'[\u0e00-\u0e7f]',
    # Cyrillic (Russian, Ukrainian, etc.)
    "cyrillic": r'[\u0400-\u04ff]',
    # Vietnamese (Latin with diacritics)
    "vietnamese": r'[ăâăắầằẩấđêĩôơưạảấầẩằắặậẽẻẹếềểễệỉịỏọốồổộớờởợụủứừửựỹỵỷ]',
    # Arabic
    "arabic": r'[\u0600-\u06ff\u0750-\u077f]',
    # Devanagari (Hindi, Sanskrit)
    "devanagari": r'[\u0900-\u097f]',
    # Tamil
    "tamil": r'[\u0b80-\u0bff]',
    # Hebrew
    "hebrew": r'[\u0590-\u05ff]',
    # Greek
    "greek": r'[\u0370-\u03ff]',
}

# Language detection using Unicode ranges
@lru_cache(maxsize=10000)
def detect_by_unicode(text: str) -> str | None:
    """Detect language by Unicode character ranges."""
    if not text or not text.strip():
        return None

    # Check for CJK characters
    if re.search(UNICODE_RANGES["chinese"], text):
        return "chinese"
    if re.search(UNICODE_RANGES["japanese"], text):
        return "japanese"
    if re.search(UNICODE_RANGES["korean"], text):
        return "korean"
    if re.search(UNICODE_RANGES["thai"], text):
        return "thai"
    if re.search(UNICODE_RANGES["cyrillic"], text):
        return "russian"  # Most common Cyrillic language
    if re.search(UNICODE_RANGES["arabic"], text):
        return "arabic"
    if re.search(UNICODE_RANGES["devanagari"], text):
        return "hindi"
    if re.search(UNICODE_RANGES["tamil"], text):
        return "tamil"
    if re.search(UNICODE_RANGES["greek"], text):
        return "greek"
    if re.search(UNICODE_RANGES["hebrew"], text):
        return "hebrew"

    return None


def build_lingua_detector():
    """Build lingua detector with 5 languages: English, Malay, Spanish, Portuguese, Indonesian."""
    return LanguageDetectorBuilder.from_languages(
        Language.ENGLISH,
        Language.MALAY,
        Language.SPANISH,
        Language.PORTUGUESE,
        Language.INDONESIAN,
    ).build()


# Global detector instance
_detector = None


def get_lingua_detector():
    """Get singleton lingua detector."""
    global _detector
    if _detector is None:
        _detector = build_lingua_detector()
    return _detector


def detect_language(text: str) -> str:
    """
    Detect language of the given text.

    Returns language name: chinese, japanese, korean, thai, russian,
    arabic, hindi, tamil, greek, hebrew, malay, spanish, portuguese,
    indonesian, or english (default).
    """
    if not text or not text.strip():
        return "english"

    text = text.strip()

    # First try Unicode-based detection for non-latin languages
    unicode_lang = detect_by_unicode(text)
    if unicode_lang:
        return unicode_lang

    # Then try lingua for latin-based languages
    try:
        detector = get_lingua_detector()
        result = detector.detect_language_of(text)
        if result:
            lang_map = {
                Language.ENGLISH: "english",
                Language.MALAY: "malay",
                Language.SPANISH: "spanish",
                Language.PORTUGUESE: "portuguese",
                Language.INDONESIAN: "indonesian",
            }
            return lang_map.get(result, "english")
    except Exception:
        pass

    # Default to English for ASCII-only text
    return "english"


if __name__ == "__main__":
    # Test
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

    for t in tests:
        print(f"{t[:30]:30} -> {detect_language(t)}")
