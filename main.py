import csv
import opencc
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
    Language.VIETNAMESE: "Vietnamese",
    Language.RUSSIAN: "Russian",
    Language.GERMAN: "German",
    Language.FRENCH: "French",
    Language.ITALIAN: "Italian",
}

# 创建OpenCC转换器
s2t_converter = opencc.OpenCC('s2t')  # 简体转繁体
t2s_converter = opencc.OpenCC('t2s')  # 繁体转简体

def is_traditional_chinese(text):
    """使用OpenCC检测文本是简体中文还是繁体中文

    原理：
    - 简体文本经过 t2s(s2t(text)) 转换后基本不变（差异小）
    - 繁体文本经过 s2t(t2s(text)) 转换后基本不变（差异小）

    通过比较两个方向的转换差异来判断文本类型。
    """
    if not text or not text.strip():
        return False

    # 纯ASCII文本不是中文
    if text.isascii():
        return False

    # 检查是否包含中文字符
    has_chinese = any("\u4e00" <= c <= "\u9fff" for c in text)
    if not has_chinese:
        return False

    # 简→繁→简
    simplified_roundtrip = t2s_converter.convert(s2t_converter.convert(text))
    # 繁→简→繁
    traditional_roundtrip = s2t_converter.convert(t2s_converter.convert(text))

    # 计算差异字符数
    diff_s = sum(1 for a, b in zip(text, simplified_roundtrip) if a != b)
    diff_t = sum(1 for a, b in zip(text, traditional_roundtrip) if a != b)

    # 如果两个方向的差异都很大，可能是混合文本或单字符（如"哈哈哈"）
    # 这种情况下，如果文本中有繁体Unicode特征字符，视为繁体
    if abs(diff_s - diff_t) <= 1:
        # 差异接近，检查Unicode特征
        TRADITIONAL_RANGES = [
            (0x3100, 0x312F),  # Bopomofo (注音符号，繁体)
            (0xF900, 0xFAFF),  # CJK Compatibility Ideographs
        ]
        for char in text:
            code = ord(char)
            for start, end in TRADITIONAL_RANGES:
                if start <= code <= end:
                    return True
        return False

    # diff_s < diff_t 说明原文更接近简体
    return diff_t < diff_s

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