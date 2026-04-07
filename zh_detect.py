"""中文简繁/粤语检测模块

提供单一函数 detect_language(text) 用于检测文本语言类型。
只检测中文（简体/繁体/粤语），其他语言返回 None。
"""

import opencc

# =============================================================================
# 常量定义
# =============================================================================

# Emoji 和符号 Unicode 范围
EMOJI_RANGES = [
    (0x2600, 0x26FF),   # Miscellaneous Symbols
    (0x2700, 0x27BF),   # Dingbats
    (0x1F300, 0x1F9FF), # Miscellaneous Symbols and Pictographs
    (0x1FA00, 0x1F6FF), # Various emoji
]

# 中文标点符号
CHINESE_PUNCTUATION = set('！？。，：；、「」『』【】（）〈〉《》……——－·')


# =============================================================================
# 初始化
# =============================================================================

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


def _is_pure_punctuation_or_emoji(text: str) -> bool:
    """检查文本是否为纯标点符号或emoji（无实际内容）"""
    for char in text:
        code = ord(char)
        # 检查是否是emoji
        is_emoji = any(start <= code <= end for start, end in EMOJI_RANGES)
        if is_emoji:
            continue
        # 检查是否是中文标点
        if char in CHINESE_PUNCTUATION:
            continue
        # 检查是否是ASCII标点
        if char in '.,!?()[]{}":;\'/-_+=*&^%$#@~`':
            continue
        # 检查是否是空格/控制字符
        if char.isspace() or ord(char) < 32:
            continue
        # 有其他字符，不是纯标点/emoji
        return False
    return True


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
    STRONG_CHAR_FEATURES = ['冇', '喺', '嘅', '哋', '咁', '咗', '唔', '睇', '俾', '攞', '搵', '咩', '嘞', '乜', '啫', '咖', '喇']
    for char in STRONG_CHAR_FEATURES:
        if char in text:
            return True

    # 其他单字级特征（需要至少2个才判定为粤语）
    # 注意：不含喇、咖，因其在 STRONG_CHAR_FEATURES 中已检测
    CHAR_FEATURES = ['噉', '吖', '喔', '咯', '噃', '咋', '啩', '啰', '嘎', '㗎']

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

    # 计算差异（考虑长度差异，较长文本的超出部分也算作差异）
    diff_s = sum(1 for i in range(len(text)) if (i >= len(to_simplified) or text[i] != to_simplified[i]))
    diff_t = sum(1 for i in range(len(text)) if (i >= len(to_traditional) or text[i] != to_traditional[i]))

    TRADITIONAL_SPECIFIC = set('絡網價過錢預賬戶郵詐騙時間麼轉賣買飛會丟並亞佇佈佔併來係倉個們倫側偵偽傑傘備傳傷僅價儘償優儲兌兒內兩冊凍別刪則剛創剷劃劍動務勢匯區協卻厭參員唄問啟喎單嗎嗰嘗嘩囉國圍圖團報場墮夠夢夾媽嬌學實審寫寵寶將專尋對導層屬峯帥帳帶幣幫幹幾庫廈廢廣廳張強彈後徑從復恆惡愛態慘慮憑應懷戶掃掛採揀換損搖搵搶撐撳擁擇擊擋擔據擠擬擺攜攤攪攬敗數斃斷於時暫書會東條棄業極榮構樂樑樓標樣機檔檢檯檻櫃欄權歐歡歲歸毀氈氣決沒沖況洩淚淨減測準溝溫滅滙滾漢漣潰濤濫瀏灘灣為無煩熱燈爛爾牆狀猶獅獎獨獲現環產畢畫異當發盜盡盤盧眾瞞確碼礙禮種稱穩筆節範簡簽籌籬紀約紅納純紙級細終結絡給統絲綁經綜線維網綴綵緊線編練縮總繫繳繼續罵習聖聯職聽脫腦腳膽臉臨臺與舉舊華萬蓋薦藍藝蘇處虛號螞蟻術衛衝裡補裝裡製複見規視親覺覽觀訂計訊託記')

    # 如果差异都很小，检查是否包含繁体特有字符
    if diff_s == 0 and diff_t == 0:
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


def _is_long_chinese_text(text: str) -> bool:
    """判断是否为长中文文本（参与历史统计）"""
    chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return chinese_count >= 5


def _has_strong_chinese_signal(text: str) -> bool:
    """判断文本是否有强中文信号（即使短文本也值得参考）"""
    if has_cantonese_features(text):
        return True
    if is_traditional_chinese(text):
        return True
    return False


def _is_valid_history_text(text: str) -> bool:
    """判断文本是否可作为有效历史参考"""
    if _is_long_chinese_text(text):
        return True
    if _has_strong_chinese_signal(text):
        return True
    # 普通中文文本（至少有汉字）
    if has_chinese(text):
        return True
    return False


def detect_language(text: str, history: list[str] | None = None) -> str | None:
    """检测文本语言（仅限中文简/繁/粤语）

    Args:
        text: 输入文本
        history: 历史文本列表，用于辅助判断短文本的语言
                例如用户连续对话中，短文本可能与之前的中文内容相关

    Returns:
        "Chinese(Simplified)", "Chinese(Traditional)", "Cantonese"
        或 None（表示非中文语言）
    """
    if not text or not text.strip():
        return None

    text = normalize_text(text)
    stripped = text.strip()

    # ASCII文本：尝试用历史辅助判断
    if stripped.isascii():
        if history:
            for hist_text in history:
                hist_normalized = normalize_text(hist_text)
                if _is_valid_history_text(hist_normalized):
                    hist_result = detect_language(hist_text, None)
                    if hist_result in ('Chinese(Simplified)', 'Chinese(Traditional)', 'Cantonese'):
                        return hist_result
        return None

    # 纯标点符号或emoji：尝试用历史辅助判断
    if _is_pure_punctuation_or_emoji(stripped):
        if history:
            for hist_text in history:
                hist_normalized = normalize_text(hist_text)
                if _is_valid_history_text(hist_normalized):
                    hist_result = detect_language(hist_text, None)
                    if hist_result in ('Chinese(Simplified)', 'Chinese(Traditional)', 'Cantonese'):
                        return hist_result
        return None

    # 短文本且有历史记录，尝试用历史辅助判断
    if not _is_long_chinese_text(stripped) and history:
        for hist_text in history:
            hist_normalized = normalize_text(hist_text)
            if _is_valid_history_text(hist_normalized):
                hist_result = detect_language(hist_text, None)
                if hist_result in ('Chinese(Simplified)', 'Chinese(Traditional)', 'Cantonese'):
                    return hist_result

    # 检查是否包含汉字
    if not has_chinese(stripped):
        return None

    # 如果包含其他语言字符（非中文），直接返回 None
    # 日语假名
    if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in stripped):
        return None
    # 韩语
    if any('\uac00' <= c <= '\ud7af' for c in stripped):
        return None
    # 俄语/西里尔字母
    if any('\u0400' <= c <= '\u04ff' for c in stripped):
        return None
    # 越南语特有字符
    if any(c in 'ăâđêôơư' for c in stripped):
        return None

    # 检测粤语
    if has_cantonese_features(stripped):
        return "Cantonese"

    # 检测繁体/简体
    if is_traditional_chinese(stripped):
        return "Chinese(Traditional)"

    return "Chinese(Simplified)"
