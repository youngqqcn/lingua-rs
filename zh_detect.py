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
# 注意：已移除"呀"（普通话常用语气词），避免误判
CANTONESE_FEATURES = [
    # 核心虚词/语气词（粤语特有，普通话少用）
    '冇', '喺', '嘅', '哋', '乜', '咗', '噉', '吖', '喔', '咯', '噃', '咋', '咁', '咩', '啫', '啩', '嘞', '啰', '喇', '咖', '嘎', '㗎',
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
    """严格检测文本是否包含明确的粤语特征词

    判定规则：
    - 任意一个词组级特征 OR
    - 任意一个高频单字特征 OR
    - 2个或以上其他单字特征

    重要：对于可能在简繁转换中混淆的字符（如點/点），只检查原文
    """
    if not text or not text.strip():
        return False
    if text.isascii():
        return False
    if not has_chinese(text):
        return False

    # 检查原文是否包含简体特有的"点"（不是繁体"點"）
    has_simplified_dian = '点' in text

    # 词组级特征（任意一个即判定为粤语）
    PHRASE_FEATURES = ['點解', '邊度', '做咩', '係咪', '係唔係', '唔該', '多謝', '真係', '你哋', '佢哋', '我哋', '搶飛', '買飛', '點樣', '點算']
    for feature in PHRASE_FEATURES:
        if feature in text:
            return True

    # 高频单字特征（出现在>5%的粤语样本中）
    # 这些字只在粤语中出现，不会与繁体/简体混淆
    # 任意一个即可判定为粤语
    STRONG_CHAR_FEATURES = ['冇', '喺', '嘅', '哋', '咁', '咗', '唔', '睇', '俾', '攞', '咩', '嘞', '乜', '啫', '咖', '喇']
    for char in STRONG_CHAR_FEATURES:
        if char in text:
            return True

    # 其他单字级特征（需要至少2个才判定为粤语）
    CHAR_FEATURES = ['噉', '吖', '喔', '咯', '噃', '咋', '啩', '啰', '喇', '咖', '嘎', '㗎']

    # 如果原文包含"点"（简体形式），不检查基于"點"的特征
    # 这样可以避免简转繁产生的误判
    if has_simplified_dian:
        return False

    char_count = 0
    for feature in CHAR_FEATURES:
        if feature in text:
            char_count += 1
            if char_count >= 2:
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

    TRADITIONAL_SPECIFIC = set('絡網價過錢預賬戶郵寄詐騙時間麼轉賣買飛會丟並亞佇佈佔併來係倉個們倫側偵偽傑傘備傳傷僅價儘償優儲兌兒內兩冊凍別刪則剛創剷劃劍動務勢匯區協卻厭參員唄問啟喎單嗎嗰嘗嘩囉國圍圖團報場墮夠夢夾媽嬌學實審寫寵寶將專尋對導層屬峯帥帳帶幣幫幹幾庫廈廢廣廳張強彈後徑從復恆惡愛態慘慮憑應懷戶掃掛採揀換損搖搵搶撐撳擁擇擊擋擔據擠擬擺攜攤攪攬敗數斃斷於時暫書會東條棄業極榮構樂樑樓標樣機檔檢檯檻櫃欄權歐歡歲歸毀氈氣決沒沖況洩淚淨減測準溝溫滅滙滾漢漣潰濤濫瀏灘灣為無煩熱燈爛爾牆狀猶獅獎獨獲現環產畢畫異當發盜盡盤盧眾瞞確碼礙禮種稱穩筆節範簡簽籌籬紀約紅納純紙級細終結絡給統絲綁經綜線維網綴綵緊線編練縮總繫繳繼續罵習聖聯職聽脫腦腳膽臉臨臺與舉舊華萬蓋薦藍藝蘇處虛號螞蟻術衛衝裡補裝裡製複見規視親覺覽觀訂計訊託記')

    # 如果差异都很小，检查是否包含繁体特有字符
    if diff_s == 0 and diff_t == 0:
        # 两个方向转换都没变化，检查是否包含繁体特有字符
        # 只有真正简繁有差异的字才算


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
        # 只有真正简繁有差异的字才算
        count = sum(1 for c in text if c in TRADITIONAL_SPECIFIC)
        return count / chinese_count > 0.3

    # 使用变化率差异判断
    # diff_s > diff_t: 需要更多变化才能变成简体 → 原文本是繁体
    # diff_t > diff_s: 需要更多变化才能变成繁体 → 原文本是简体
    # 但需要满足最小阈值才判定
    diff_diff = diff_s - diff_t
    if abs(diff_diff) < 2:
        # 差异太小，使用字符统计
        # 只有真正简繁有差异的字才算
        count = sum(1 for c in text if c in TRADITIONAL_SPECIFIC)
        return count / chinese_count > 0.3

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
