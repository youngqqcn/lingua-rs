import csv
import re
from collections import defaultdict
from lingua import Language, LanguageDetectorBuilder
import opencc

# 短文本最大长度
SHORT_TEXT_MAX_LEN = 10

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

# 中文关键词
CHINESE_KEYWORDS = [
    '演唱会', '门票', '在哪里', '什么时候', '粉丝', '位置', '座位', '香港', '澳门',
    '付款', '支付', '微信', '支付宝', '零钱', '转账', '收款', '信用卡',
    '电子码', '纸质', '二维码', '入场', '进场', '转赠', '转让', '周边',
    '认证', '验证', '实名', '登记', '注册',
    '出票', '发货', '到达', '开始', '结束', '开场',
    '座位号', '座位分配', '专区', '区域', '票价', '价格', '多少钱',
    '有什么', '哪些', '怎么', '如何', '请问', '想问', '问一下',
    '场次', '排期', '日程', '日程表', '几时', '出日程',
    '购买', '发售', '开售', '购票', '买票', '抢票',
    '什麼', '什麼是', '啥', '吗', '呢', '嘛',
    '是', '在', '找', '买', '賣', '卖', '送', '换', '兑', '查', '看',
    '意思', '方法', '方式', '时间', '时间表', '版本', '链接', '邮件', '電郵',
    '票夹', '票务', '会员', '代码',
    '有没有', '可以嗎', '可以吗', '能不能', '会不会',
    '马来西亚', '吉隆坡', 'penang', '槟城', '三亚', '海口',
]

# 单字中文字符
SINGLE_CHINESE_CHARS = [
    '排', '区', '层', '座', '号', '厢',
    '呢', '吗', '嘛', '啥', '哪', '谁',
    '的', '了', '在', '是', '我', '你', '他', '她', '它', '有', '没', '会', '能', '可', '以', '要', '想', '请', '问', '帮', '查', '看', '买', '卖', '送', '换', '兑', '得', '拿', '取', '收', '入', '出',
    '時間', '時', '間', '國', '際', '郵', '件', '電', '請', '問', '購買',
    '賣', '贈', '送', '兌', '換', '號', '碼', '區', '層', '座', '排', '廂',
    '確', '認', '證', '識', '別', '驗', '實', '名', '登', '記', '註', '冊',
    '發', '貨', '到', '達', '開', '始', '結', '束', '場', '入', '進', '轉', '讓',
]

# 中文标点符号
CHINESE_PUNCTUATION = [
    '？', '！', '，', '。', '：', '；', '、', '「', '」', '『', '』', '【', '】', '（', '）',
    '﹁', '﹂', '﹃', '﹄', '《', '》', '〈', '〉',
    '……', '——', '－',
    '·',
]

# 中文起始词
CHINESE_START_WORDS = [
    '好', '请问', '想问', '问一下', '帮我', '帮我查', '帮我找',
    '你好', '您好', '麻烦', '请教', '想问一下', '请问一下',
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



def has_chinese_keywords(text):
    """检测是否包含中文关键词"""
    for keyword in CHINESE_KEYWORDS:
        if keyword in text:
            return True
    for char in SINGLE_CHINESE_CHARS:
        if char in text:
            return True
    for word in CHINESE_START_WORDS:
        if text.startswith(word):
            return True
    for punct in CHINESE_PUNCTUATION:
        if punct in text:
            return True
    return False


def normalize_text(text):
    """标准化文本：移除特殊引号等干扰字符"""
    # 替换各种特殊的引号为普通 apostrophe
    text = text.replace('\u2018', "'")  # LEFT SINGLE QUOTATION MARK
    text = text.replace('\u2019', "'")  # RIGHT SINGLE QUOTATION MARK
    text = text.replace('\u201a', "'")  # SINGLE LOW-9 QUOTATION MARK
    text = text.replace('\u201b', "'")  # SINGLE HIGH-REVERSED-9 QUOTATION MARK
    text = text.replace('\u2032', "'")  # PRIME
    text = text.replace('\u2035', "'")  # REVERSED PRIME
    # 替换双引号变体
    text = text.replace('\u201c', '"')  # LEFT DOUBLE QUOTATION MARK
    text = text.replace('\u201d', '"')  # RIGHT DOUBLE QUOTATION MARK
    text = text.replace('\u201e', '"')  # DOUBLE LOW-9 QUOTATION MARK
    text = text.replace('\u201f', '"')  # DOUBLE HIGH-REVERSED-9 QUOTATION MARK
    # 替换特殊破折号/连字符
    text = text.replace('\u2014', '-')  # EM DASH
    text = text.replace('\u2013', '-')  # EN DASH
    text = text.replace('\u2010', '-')  # HYPHEN
    text = text.replace('\u2011', '-')  # NON-BREAKING HYPHEN
    # 替换特殊数字字符为普通字符
    text = text.replace('\u2160', 'I')  # ROMAN NUMERAL ONE
    text = text.replace('\u2161', 'II')
    text = text.replace('\u2162', 'III')
    text = text.replace('\u2163', 'IV')
    text = text.replace('\u2164', 'V')
    text = text.replace('\u2165', 'VI')
    text = text.replace('\u2166', 'VII')
    text = text.replace('\u2167', 'VIII')
    text = text.replace('\u2168', 'IX')
    text = text.replace('\u2169', 'X')
    text = text.replace('\u2170', 'i')  # SMALL ROMAN NUMERAL ONE
    text = text.replace('\u2171', 'ii')
    text = text.replace('\u2172', 'iii')
    text = text.replace('\u2173', 'iv')
    text = text.replace('\u2174', 'v')
    text = text.replace('\u2175', 'vi')
    text = text.replace('\u2176', 'vii')
    text = text.replace('\u2177', 'viii')
    text = text.replace('\u2178', 'ix')
    text = text.replace('\u2179', 'x')  # SMALL ROMAN NUMERAL TEN
    # 上标数字
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

    # 移除间隔符后再处理
    for sep in ['\u200b', '\u200c', '\u200d', '\u2060', '\u2006', '\u200a', '\u202f', '\u00a0']:
        stripped = stripped.replace(sep, '')

    # 纯数字过滤
    if PURE_NUMBER_PATTERN.match(stripped):
        return True

    # Booking code 过滤
    if BOOKING_CODE_PATTERN.match(stripped):
        return True

    # 判断是英文还是中文
    is_ascii = stripped.isascii()
    has_chinese = any("\u4e00" <= c <= "\u9fff" for c in stripped)

    if is_ascii:
        # 英文：需要至少5个单词
        word_count = len(stripped.split())
        if word_count < 5:
            return True
    elif has_chinese:
        # 中文：需要至少5个汉字
        chinese_char_count = sum(1 for c in stripped if "\u4e00" <= c <= "\u9fff")
        if chinese_char_count < 5:
            return True
    else:
        # 混合或其他：总字符数少于5
        if len(stripped) < 5:
            return True

    return False


# =============================================================================
# 语言检测函数
# =============================================================================

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


def detect_language(text):
    """使用lingua-py检测文本语言，直接返回清洗后的结果"""
    if not text or not text.strip():
        return None  # 返回None表示需要过滤

    stripped = text.strip()

    # ========== 前置过滤 ==========

    # 短文本/纯数字过滤
    if should_filter_short_text(stripped):
        return None


    # ========== 语言检测 ==========

    # 标准化文本：移除特殊引号干扰
    text = normalize_text(text)

    if text.isascii():
        return "English"

    # 移除emoji后检查是否为纯英文（处理带emoji的英文文本被误判的问题）
    text_no_emoji = remove_emoji(text)
    if text_no_emoji.isascii() and text_no_emoji.strip():
        return "English"

    try:
        lang = detector.detect_language_of(text)

        if lang == Language.CHINESE:
            # 中文优先检测粤语
            if has_cantonese_features(text):
                return "Cantonese"
            if is_traditional_chinese(text):
                return "Chinese(Traditional)"
            return "Chinese(Simplified)"

        # 非中文语言才进行重新分类检查
        if lang is not None:
            detected = LANG_NAME_MAP.get(lang, str(lang))

            # 回退：如果文本包含中文字符、中文标点或日文假名，使用检测逻辑
            has_cjk = any("\u4e00" <= c <= "\u9fff" for c in text)
            has_chinese_punct = any(p in text for p in CHINESE_PUNCTUATION)
            has_hiragana = any("\u3040" <= c <= "\u309f" for c in text)
            has_katakana = any("\u30a0" <= c <= "\u30ff" for c in text)
            has_thai = any("\u0e00" <= c <= "\u0e7f" for c in text)
            has_hangul = any("\uac00" <= c <= "\ud7af" for c in text)
            has_cyrillic = any("\u0400" <= c <= "\u04ff" for c in text)
            # 越南语特定字符范围：ă, â, đ, ê, ô, ơ, ư (及其带声调符号)
            # 越南语特定字符：ă, â, đ, ê, ô, ơ, ư
            has_vietnamese = any(c in 'ăâđêôơư' for c in text)

            # 检测拉丁文本中混有西里尔近似字符的情况（如歌词中的错字）
            # 如果拉丁字母远多于西里尔字母，说明是拉丁文本被误判
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

            # 回退：如果包含日文假名，判定为日语
            if has_hiragana or has_katakana:
                return "Japanese"

            # 回退：如果包含泰语字符，判定为泰语
            if has_thai:
                return "Thai"

            # 回退：如果包含俄语字符（西里尔字母），判定为俄语
            # 但如果文本主要是拉丁字母混有少量西里尔错字，则不判定为俄语
            if has_cyrillic and not is_latin_with_cyrillic_mix:
                return "Russian"

            # 回退：如果包含越南语气符（拉丁字母带变音符号），判定为越南语
            if has_vietnamese:
                return "Vietnamese"

            return detected
        return "Unknown"
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

        return "Unknown"


# =============================================================================
# 主函数
# =============================================================================

def main():
    input_file = "data1.csv"
    output_file = "result2.csv"

    stats = {
        'total': 0,
        'filtered': 0,
    }

    rows = []
    with open(input_file, "r", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        for row in reader:
            stats['total'] += 1
            user_id = row["user_id"]
            content = row["content"]
            language = detect_language(content)

            if language is None:
                # 过滤掉
                stats['filtered'] += 1
            else:
                rows.append({
                    "user_id": user_id,
                    "content": content,
                    "language": language
                })

    # 写入 result2.csv
    with open(output_file, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["user_id", "content", "language"])
        writer.writeheader()
        writer.writerows(rows)

    # 生成 statistic.csv
    user_lang_counts = defaultdict(lambda: defaultdict(int))
    for row in rows:
        user_lang_counts[row["user_id"]][row["language"]] += 1

    all_languages = sorted(set(
        lang for user_counts in user_lang_counts.values()
        for lang in user_counts.keys()
    ))

    with open("statistic.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id"] + all_languages)
        writer.writeheader()
        for user_id in sorted(user_lang_counts.keys()):
            row = {"user_id": user_id}
            for lang in all_languages:
                row[lang] = user_lang_counts[user_id][lang]
            writer.writerow(row)

    # 打印报告
    print("=" * 50)
    print("处理完成")
    print("=" * 50)
    print(f"总记录数: {stats['total']}")
    print(f"被过滤: {stats['filtered']}")
    print(f"有效记录: {len(rows)}")
    print(f"\nresult2.csv 和 statistic.csv 已生成")


if __name__ == "__main__":
    main()