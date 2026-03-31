import csv
from lingua import Language, LanguageDetectorBuilder

# 创建语言检测器
languages = [
    Language.CHINESE,
    Language.ENGLISH,
    Language.JAPANESE,
    Language.KOREAN,
    Language.MALAY,
    Language.SPANISH,
    Language.PORTUGUESE,
    Language.INDONESIAN,
]
detector = LanguageDetectorBuilder.from_languages(*languages).build()

# lingua Language枚举到英文名称的映射
LANG_NAME_MAP = {
    Language.CHINESE: "Chinese(Simplified)",  # 默认视为简体
    Language.ENGLISH: "English",
    Language.JAPANESE: "Japanese",
    Language.KOREAN: "Korean",
    Language.MALAY: "Malay",
    Language.SPANISH: "Spanish",
    Language.PORTUGUESE: "Portuguese",
    Language.INDONESIAN: "Indonesian",
}

# 繁体中文Unicode区间（用于区分简繁体）
# 繁体中文常用字范围：CJK兼容表意文字 U+2F00-U+2FD5, U+3000-U+303F, U+3100-U+312F, U+3200-U+32FF
TRADITIONAL_CHINESE_RANGES = [
    (0x2F00, 0x2FD5),  # Kangxi Radicals
    (0x3000, 0x303F),  # CJK Symbols and Punctuations (部分繁體有用)
    (0x3100, 0x312F),  # Bopomofo (注音符号，繁体)
    (0x3200, 0x32FF),  # Enclosed CJK Letters (部分繁体)
    (0xF900, 0xFAFF),  # CJK Compatibility Ideographs (繁体兼容字)
    (0x20000, 0x2A6DF),  # CJK Unified Ideographs Extension B-G (罕见繁体字)
    (0x2A700, 0x2B73F),  # CJK Unified Ideographs Extension (罕见繁体字)
    (0x2B740, 0x2B81F),  # CJK Unified Ideographs Extension (罕见繁体字)
    (0x2B820, 0x2CEAF),  # CJK Unified Ideographs Extension (罕见繁体字)
]

def is_traditional_chinese(text):
    """检测文本是否包含繁体中文"""
    for char in text:
        code = ord(char)
        for start, end in TRADITIONAL_CHINESE_RANGES:
            if start <= code <= end:
                return True
    return False

def detect_language(text):
    """使用lingua-py检测文本语言，返回英文语言名称"""
    if not text or not text.strip():
        return "Unknown"

    # 纯ASCII文本直接返回English
    if text.isascii():
        return "English"

    try:
        lang = detector.detect_language_of(text)

        # 特殊处理中文：检查是否为繁体
        if lang == Language.CHINESE:
            if is_traditional_chinese(text):
                return "Chinese(Traditional)"
            return "Chinese(Simplified)"

        if lang is not None:
            return LANG_NAME_MAP.get(lang, str(lang))
        return "Unknown"
    except Exception:
        # 回退：使用Unicode区间检测
        has_cjk = any("\u4e00" <= c <= "\u9fff" for c in text)
        has_hiragana = any("\u3040" <= c <= "\u309f" for c in text)
        has_katakana = any("\u30a0" <= c <= "\u30ff" for c in text)
        has_hangul = any("\uac00" <= c <= "\ud7af" for c in text)

        if has_hiragana or has_katakana:
            return "Japanese"
        if has_hangul:
            return "Korean"
        if has_cjk:
            if is_traditional_chinese(text):
                return "Chinese(Traditional)"
            return "Chinese(Simplified)"

        return "Unknown"

def main():
    input_file = "data1.csv"
    output_file = "result2.csv"

    with open(input_file, "r", encoding="utf-8") as f_in, \
         open(output_file, "w", encoding="utf-8", newline="") as f_out:

        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=["user_id", "content", "language"])
        writer.writeheader()

        for row in reader:
            user_id = row["user_id"]
            content = row["content"]
            language = detect_language(content)
            writer.writerow({
                "user_id": user_id,
                "content": content,
                "language": language
            })

    print(f"处理完成，结果已保存到 {output_file}")

if __name__ == "__main__":
    main()