"""语言检测模块

提供单一函数 detect_language(text) 用于检测文本语言类型。
支持：中文（简体/繁体/粤语）、英语、日语、韩语、泰语、俄语、越南语等。
"""

import re
from lingua import Language, LanguageDetectorBuilder
import opencc

# =============================================================================
# 常量定义
# =============================================================================

# 粤语特征词表
CANTONESE_FEATURES = [
    '冇', '喺', '嘅', '哋', '乜', '咗', '噉',
    '點解', '邊度', '做咩', '係咪', '係唔係', '唔該', '多謝', '真係', '你哋', '佢哋',
    '㗎', '咩', '啫', '啩', '嘞', '啰', '喇', '咖', '嘎',
    '諗', '攞', '掂', '睇', '搵', '搶飛', '買飛'
]

# lingua 语言映射
LANG_NAME_MAP = {
    Language.CHINESE: "Chinese(Simplified)",
    Language.ENGLISH: "English",
    Language.JAPANESE: "Japanese",
    Language.KOREAN: "Korean",
    Language.MALAY: "Malay",
    Language.SPANISH: "Spanish",
    Language.PORTUGUESE: "Portuguese",
    Language.INDONESIAN: "Indonesian",
    Language.VIETNAMESE: "Vietnamese",
    Language.RUSSIAN: "Russian",
    Language.THAI: "Thai",
}

# 过滤模式
PURE_NUMBER_PATTERN = re.compile(r'^\d{5,}$')
BOOKING_CODE_PATTERN = re.compile(r'^(RB|BC|PC|TC)\d+$', re.IGNORECASE)

# 中文标点符号
CHINESE_PUNCTUATION = [
    '？', '！', '，', '。', '：', '；', '、', '「', '」', '『', '』', '【', '】', '（', '）',
    '﹁', '﹂', '﹃', '﹄', '《', '》', '〈', '〉',
    '……', '——', '－',
    '·',
]

# Emoji和符号 Unicode 范围
EMOJI_RANGES = [
    (0x2600, 0x26FF),   # Miscellaneous Symbols
    (0x2700, 0x27BF),   # Dingbats
    (0x1F300, 0x1F9FF), # Miscellaneous Symbols and Pictographs
    (0x1FA00, 0x1F6FF), # Various emoji
]


# =============================================================================
# 初始化
# =============================================================================

s2t_converter = opencc.OpenCC('s2t')
t2s_converter = opencc.OpenCC('t2s')

languages = [
    Language.CHINESE,
    Language.ENGLISH,
    Language.JAPANESE,
    Language.KOREAN,
    Language.MALAY,
    Language.SPANISH,
    Language.PORTUGUESE,
    Language.INDONESIAN,
    Language.VIETNAMESE,
    Language.RUSSIAN,
    Language.THAI,
]
detector = LanguageDetectorBuilder.from_languages(*languages).build()


# =============================================================================
# 工具函数
# =============================================================================

def normalize_text(text):
    """标准化文本：移除特殊引号等干扰字符"""
    text = text.replace('\u2018', "'")   # LEFT SINGLE QUOTATION MARK
    text = text.replace('\u2019', "'")   # RIGHT SINGLE QUOTATION MARK
    text = text.replace('\u201a', "'")   # SINGLE LOW-9 QUOTATION MARK
    text = text.replace('\u201b', "'")   # SINGLE HIGH-REVERSED-9 QUOTATION MARK
    text = text.replace('\u2032', "'")   # PRIME
    text = text.replace('\u2035', "'")   # REVERSED PRIME
    text = text.replace('\u201c', '"')  # LEFT DOUBLE QUOTATION MARK
    text = text.replace('\u201d', '"')  # RIGHT DOUBLE QUOTATION MARK
    text = text.replace('\u201e', '"')  # DOUBLE LOW-9 QUOTATION MARK
    text = text.replace('\u201f', '"')  # DOUBLE HIGH-REVERSED-9 QUOTATION MARK
    text = text.replace('\u2014', '-')  # EM DASH
    text = text.replace('\u2013', '-')  # EN DASH
    text = text.replace('\u2010', '-')  # HYPHEN
    text = text.replace('\u2011', '-')  # NON-BREAKING HYPHEN
    text = text.replace('\u2160', 'I')
    text = text.replace('\u2161', 'II')
    text = text.replace('\u2162', 'III')
    text = text.replace('\u2163', 'IV')
    text = text.replace('\u2164', 'V')
    text = text.replace('\u2165', 'VI')
    text = text.replace('\u2166', 'VII')
    text = text.replace('\u2167', 'VIII')
    text = text.replace('\u2168', 'IX')
    text = text.replace('\u2169', 'X')
    text = text.replace('\u2170', 'i')
    text = text.replace('\u2171', 'ii')
    text = text.replace('\u2172', 'iii')
    text = text.replace('\u2173', 'iv')
    text = text.replace('\u2174', 'v')
    text = text.replace('\u2175', 'vi')
    text = text.replace('\u2176', 'vii')
    text = text.replace('\u2177', 'viii')
    text = text.replace('\u2178', 'ix')
    text = text.replace('\u2179', 'x')
    text = text.replace('\u00b2', '2')  # SUPERSCRIPT TWO
    text = text.replace('\u00b3', '3')  # SUPERSCRIPT THREE
    text = text.replace('\u00b9', '1')  # SUPERSCRIPT ONE
    return text


def remove_emoji(text):
    """移除文本中的emoji字符"""
    result = []
    for char in text:
        code = ord(char)
        is_emoji = False
        for start, end in EMOJI_RANGES:
            if start <= code <= end:
                is_emoji = True
                break
        if not is_emoji:
            result.append(char)
    return ''.join(result)


def should_filter_short_text(text):
    """判断短文本是否需要过滤"""
    stripped = text.strip()
    for sep in ['\u200b', '\u200c', '\u200d', '\u2060', '\u2006', '\u200a', '\u202f', '\u00a0']:
        stripped = stripped.replace(sep, '')
    if PURE_NUMBER_PATTERN.match(stripped):
        return True
    if BOOKING_CODE_PATTERN.match(stripped):
        return True
    is_ascii = stripped.isascii()
    has_chinese = any("\u4e00" <= c <= "\u9fff" for c in stripped)
    if is_ascii:
        word_count = len(stripped.split())
        if word_count < 5:
            return True
    elif has_chinese:
        chinese_char_count = sum(1 for c in stripped if "\u4e00" <= c <= "\u9fff")
        if chinese_char_count < 5:
            return True
    else:
        if len(stripped) < 5:
            return True
    return False


def has_cantonese_features(text):
    """严格检测文本是否包含明确的粤语特征词"""
    if not text or not text.strip():
        return False
    if text.isascii():
        return False
    has_chinese = any("\u4e00" <= c <= "\u9fff" for c in text)
    if not has_chinese:
        return False
    traditional_text = s2t_converter.convert(text)
    for feature in CANTONESE_FEATURES:
        if feature in traditional_text or feature in text:
            return True
    return False


def is_traditional_chinese(text):
    """使用OpenCC检测文本是简体中文还是繁体中文"""
    if not text or not text.strip():
        return False
    if text.isascii():
        return False
    has_chinese = any("\u4e00" <= c <= "\u9fff" for c in text)
    if not has_chinese:
        return False
    simplified_roundtrip = t2s_converter.convert(s2t_converter.convert(text))
    traditional_roundtrip = s2t_converter.convert(t2s_converter.convert(text))
    diff_s = sum(1 for a, b in zip(text, simplified_roundtrip) if a != b)
    diff_t = sum(1 for a, b in zip(text, traditional_roundtrip) if a != b)
    if abs(diff_s - diff_t) <= 1:
        TRADITIONAL_RANGES = [(0x3100, 0x312F), (0xF900, 0xFAFF)]
        for char in text:
            code = ord(char)
            for start, end in TRADITIONAL_RANGES:
                if start <= code <= end:
                    return True
        return False
    return diff_t < diff_s


# =============================================================================
# 语言检测函数
# =============================================================================

def detect_language(text: str) -> str | None:
    """检测文本语言

    Args:
        text: 输入文本

    Returns:
        语言字符串，如 "English", "Chinese(Simplified)", "Cantonese" 等
        返回 None 表示文本被过滤（短文本等）
    """
    if not text or not text.strip():
        return None

    # ========== 语言检测 ==========
    text = normalize_text(text)

    if text.isascii():
        return "English"

    text_no_emoji = remove_emoji(text)
    if text_no_emoji.isascii() and text_no_emoji.strip():
        return "English"

    try:
        lang = detector.detect_language_of(text)

        if lang == Language.CHINESE:
            if has_cantonese_features(text):
                return "Cantonese"
            if is_traditional_chinese(text):
                return "Chinese(Traditional)"
            return "Chinese(Simplified)"

        if lang is not None:
            detected = LANG_NAME_MAP.get(lang, str(lang))

            has_cjk = any("\u4e00" <= c <= "\u9fff" for c in text)
            has_chinese_punct = any(p in text for p in CHINESE_PUNCTUATION)
            has_hiragana = any("\u3040" <= c <= "\u309f" for c in text)
            has_katakana = any("\u30a0" <= c <= "\u30ff" for c in text)
            has_thai = any("\u0e00" <= c <= "\u0e7f" for c in text)
            has_hangul = any("\uac00" <= c <= "\ud7af" for c in text)
            has_cyrillic = any("\u0400" <= c <= "\u04ff" for c in text)
            has_vietnamese = any(c in 'ăâđêôơư' for c in text)

            latin_count = sum(1 for c in text if c.isascii() and c.isalpha())
            cyrillic_count = sum(1 for c in text if "\u0400" <= c <= "\u04ff")
            is_latin_with_cyrillic_mix = (cyrillic_count > 0 and
                                           cyrillic_count < 3 and
                                           latin_count > cyrillic_count * 5)

            if has_cjk or has_chinese_punct:
                if has_cantonese_features(text):
                    return "Cantonese"
                if is_traditional_chinese(text):
                    return "Chinese(Traditional)"
                return "Chinese(Simplified)"

            if has_hiragana or has_katakana:
                return "Japanese"

            if has_hangul:
                return "Korean"

            if has_thai:
                return "Thai"

            if has_cyrillic and not is_latin_with_cyrillic_mix:
                return "Russian"

            if has_vietnamese:
                return "Vietnamese"

            return detected
        return "English"
    except Exception:
        has_cjk = any("\u4e00" <= c <= "\u9fff" for c in text)
        has_hiragana = any("\u3040" <= c <= "\u309f" for c in text)
        has_katakana = any("\u30a0" <= c <= "\u30ff" for c in text)
        has_hangul = any("\uac00" <= c <= "\ud7af" for c in text)
        has_thai = any("\u0e00" <= c <= "\u0e7f" for c in text)
        has_cyrillic = any("\u0400" <= c <= "\u04ff" for c in text)
        has_vietnamese = any(c in 'ăâđêôơư' for c in text)

        if has_hiragana or has_katakana:
            return "Japanese"
        if has_hangul:
            return "Korean"
        if has_thai:
            return "Thai"
        if has_cyrillic:
            return "Russian"
        if has_vietnamese:
            return "Vietnamese"
        if has_cjk:
            if is_traditional_chinese(text):
                return "Chinese(Traditional)"
            return "Chinese(Simplified)"

        return "English"
