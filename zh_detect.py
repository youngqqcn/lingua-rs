"""中文简繁/粤语检测模块

提供单一函数 detect_language(text) 用于检测文本语言类型。
只检测中文（简体/繁体/粤语），其他语言返回 None。
"""

import re
import opencc

# =============================================================================
# 常量定义
# =============================================================================

# 粤语特征词表（只包含真正粤语特有的词/字，避免与繁体混淆）
CANTONESE_FEATURES = [
    # 核心虚词/语气词（粤语特有，普通话少用）
    '冇', '喺', '嘅', '哋', '乜', '咗', '噉', '吖', '喔', '呀', '咯', '噃', '咋', '咁', '咩', '啫', '啩', '嘞', '啰', '喇', '咖', '嘎', '㗎',
    # 常用词组（明确粤语特征）
    '點解', '邊度', '做咩', '係咪', '係唔係', '唔該', '多謝', '真係', '你哋', '佢哋', '我哋',
    # 动词/形容词（明确粤语）
    '諗', '攞', '掂', '睇', '搵', '搶飛', '買飛',
]

# OpenCC 转换器
s2t_converter = opencc.OpenCC('s2t')
t2s_converter = opencc.OpenCC('t2s')


# =============================================================================
# 工具函数
# =============================================================================

def normalize_text(text: str) -> str:
    """标准化文本：移除特殊字符干扰"""
    # 替换各种特殊引号
    text = text.replace('\u2018', "'")
    text = text.replace('\u2019', "'")
    text = text.replace('\u201a', "'")
    text = text.replace('\u201b', "'")
    text = text.replace('\u2032', "'")
    text = text.replace('\u2035', "'")
    text = text.replace('\u201c', '"')
    text = text.replace('\u201d', '"')
    text = text.replace('\u201e', '"')
    text = text.replace('\u201f', '"')
    # 替换特殊破折号
    text = text.replace('\u2014', '-')
    text = text.replace('\u2013', '-')
    text = text.replace('\u2010', '-')
    text = text.replace('\u2011', '-')
    # 替换罗马数字
    for old, new in [('Ⅰ','I'), ('Ⅱ','II'), ('Ⅲ','III'), ('Ⅳ','IV'), ('Ⅴ','V'),
                     ('Ⅵ','VI'), ('Ⅶ','VII'), ('Ⅷ','VIII'), ('Ⅸ','IX'), ('Ⅹ','X'),
                     ('ⅰ','i'), ('ⅱ','ii'), ('ⅲ','iii'), ('ⅳ','iv'), ('ⅴ','v'),
                     ('ⅵ','vi'), ('ⅶ','vii'), ('ⅷ','viii'), ('ⅸ','ix'), ('ⅹ','x')]:
        text = text.replace(old, new)
    return text


def has_chinese(text: str) -> bool:
    """检查是否包含汉字"""
    return any('\u4e00' <= c <= '\u9fff' for c in text)


def has_cantonese_features(text: str) -> bool:
    """严格检测文本是否包含明确的粤语特征词"""
    if not text or not text.strip():
        return False
    if text.isascii():
        return False
    if not has_chinese(text):
        return False
    # 转换为繁体后检查（粤语特征在繁体中更明显）
    traditional_text = s2t_converter.convert(text)
    for feature in CANTONESE_FEATURES:
        if feature in traditional_text or feature in text:
            return True
    return False


def is_traditional_chinese(text: str) -> bool:
    """使用OpenCC检测文本是简体中文还是繁体中文

    原理：
    - 原文转简体后变化大 → 原文中很多繁体字 → Traditional
    - 原文转繁体后变化大 → 原文中很多简体字 → Simplified
    """
    if not text or not text.strip():
        return False
    if text.isascii():
        return False
    if not has_chinese(text):
        return False

    # 原文转简体
    to_simplified = t2s_converter.convert(text)
    # 原文转繁体
    to_traditional = s2t_converter.convert(text)

    # 计算差异
    diff_s = sum(1 for a, b in zip(text, to_simplified) if a != b)
    diff_t = sum(1 for a, b in zip(text, to_traditional) if a != b)

    # 如果差异都很小，检查是否包含繁体特有字符
    if diff_s == 0 and diff_t == 0:
        # 两个方向转换都没变化，检查是否包含繁体特有字符
        # 繁体特有字符集合（这些字在简体中完全不同）
        # 繁体特有字符（这些字在简体中完全不同）
        TRADITIONAL_SPECIFIC = set('學國會時們個來為與開關動術經業現長門間書見幾臺說認計處話號備賣質預員場樣機東車區報應響電實單導入還進這遠違運鄉鎮鏡麗總統總統鬱悶發財頭髮飛機優惠髮型時尚客戶服務頭髮')
        for char in text:
            if char in TRADITIONAL_SPECIFIC:
                return True
        return False

    # 计算汉字总数
    chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')

    if chinese_count == 0:
        return False

    # 计算变化率
    change_rate_s = diff_s / chinese_count
    change_rate_t = diff_t / chinese_count

    # 如果变化率都很低，使用繁体特征字符判断
    if change_rate_s < 0.1 and change_rate_t < 0.1:
        TRADITIONAL_SPECIFIC = set('學國會時們個來為與開關動術經業現長門間書見幾臺說認計處話號備賣質預員場樣機東車區報應響電實單導入還進這遠違運鄉鎮鏡麗總統鬱悶發財頭髮飛機優惠髮型時尚客戶服務')
        count = sum(1 for c in text if c in TRADITIONAL_SPECIFIC)
        return count / chinese_count > 0.3

    # 变化率差异判断
    return diff_s > diff_t


def detect_language(text: str) -> str | None:
    """检测文本语言（仅限中文简/繁/粤语）

    Args:
        text: 输入文本

    Returns:
        "Chinese(Simplified)", "Chinese(Traditional)", "Cantonese"
        或 None（表示非中文语言）
    """
    if not text or not text.strip():
        return None

    text = normalize_text(text)

    # 非中文文本直接返回 None
    if text.isascii():
        return None

    # 检查是否包含汉字
    if not has_chinese(text):
        return None

    # 如果包含其他语言字符（非中文），直接返回 None
    # 日语假名
    if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in text):
        return None
    # 韩语
    if any('\uac00' <= c <= '\ud7af' for c in text):
        return None
    # 俄语/西里尔字母
    if any('\u0400' <= c <= '\u04ff' for c in text):
        return None
    # 越南语特有字符
    if any(c in 'ăâđêôơư' for c in text):
        return None

    # 检测粤语
    if has_cantonese_features(text):
        return "Cantonese"

    # 检测繁体/简体
    if is_traditional_chinese(text):
        return "Chinese(Traditional)"

    return "Chinese(Simplified)"
