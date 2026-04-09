#!/usr/bin/env python3
"""
Language detection v2 - Unified detector combining:
- Unicode detection for CJK/Thai/Cyrillic/etc.
- OpenCC-based Chinese variant detection (Simplified/Traditional/Cantonese)
- lingua-slim (English, French, Malay, Spanish, Portuguese, Indonesian) for Latin-based languages

Install: pip install lingua-slim opencc-python-reimplemented
"""

import re
from typing import Optional

import opencc
from lingua import Language, LanguageDetectorBuilder


# =============================================================================
# Chinese Detection - Constants (from zh_detect.py)
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

# OpenCC 转换器
_S2T_CONVERTER = opencc.OpenCC('s2t')
_T2S_CONVERTER = opencc.OpenCC('t2s')


# =============================================================================
# LanguageDetector Class
# =============================================================================

class LanguageDetector:
    """
    Unified language detector combining:
    - Unicode-based detection for CJK/Thai/Cyrillic/etc.
    - OpenCC-based Chinese variant detection (Simplified/Traditional/Cantonese)
    - lingua-slim for Latin-based language detection

    Supported languages:
    - Chinese variants: Chinese(Simplified), Chinese(Traditional), Cantonese
    - Unicode-based: Japanese, Korean, Thai, Russian, Arabic, Hindi, Tamil, Greek, Hebrew, Vietnamese
    - lingua-slim: English, French, Malay, Spanish, Portuguese, Indonesian
    """

    # Unicode ranges for various languages/scripts
    UNICODE_RANGES = {
        "Japanese": r'[\u3040-\u309f\u30a0-\u30ff]',
        "Korean": r'[\uac00-\ud7af\u1100-\u11ff]',
        "Thai": r'[\u0e00-\u0e7f]',
        "Cyrillic": r'[\u0400-\u04ff]',
        "Arabic": r'[\u0600-\u06ff\u0750-\u077f]',
        "Devanagari": r'[\u0900-\u097f]',
        "Tamil": r'[\u0b80-\u0bff]',
        "Hebrew": r'[\u0590-\u05ff]',
        "Greek": r'[\u0370-\u03ff]',
    }

    # Vietnamese diacritics - more selective to avoid false positives
    # Only highly distinctive ones; đ is most unique to Vietnamese
    VIETNAMESE_DIACRITICS = set('ăâđêôơưấầẩẫắầẩẫặậẽẹềểễệỉọỏốồổộớờởợụủứừửự')
    VIETNAMESE_MIN_DIACRITICS = 2

    # Map lingua Language enum to display names
    LINGUA_LANG_MAP = {
        Language.ENGLISH: "English",
        Language.FRENCH: "French",
        Language.MALAY: "Malay",
        Language.SPANISH: "Spanish",
        Language.PORTUGUESE: "Portuguese",
        Language.INDONESIAN: "Indonesian",
    }

    # Strong languages that can help determine short text language
    STRONG_LANGUAGES = {
        "Chinese(Simplified)", "Chinese(Traditional)", "Cantonese",
        "Japanese", "Korean", "Thai", "Russian",
        "Arabic", "Hindi", "Tamil", "Greek", "Hebrew", "Vietnamese"
    }

    def __init__(self):
        """Initialize the detector."""
        self._detector = None

    # =========================================================================
    # Utility Methods (from zh_detect.py)
    # =========================================================================

    def _normalize_text(self, text: str) -> str:
        """标准化文本：移除特殊字符干扰"""
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u201a', "'").replace('\u201b', "'")
        text = text.replace('\u2032', "'").replace('\u2035', "'")
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        text = text.replace('\u201e', '"').replace('\u201f', '"')
        text = text.replace('\u2014', '-').replace('\u2013', '-')
        text = text.replace('\u2010', '-').replace('\u2011', '-')
        for old, new in [('Ⅰ','I'), ('Ⅱ','II'), ('Ⅲ','III'), ('Ⅳ','IV'), ('Ⅴ','V'),
                         ('Ⅵ','VI'), ('Ⅶ','VII'), ('Ⅷ','VIII'), ('Ⅸ','IX'), ('Ⅹ','X'),
                         ('ⅰ','i'), ('ⅱ','ii'), ('ⅲ','iii'), ('ⅳ','iv'), ('ⅴ','v'),
                         ('ⅵ','vi'), ('ⅶ','vii'), ('ⅷ','viii'), ('ⅸ','ix'), ('ⅹ','x')]:
            text = text.replace(old, new)
        return text

    def _has_chinese(self, text: str) -> bool:
        """检查是否包含汉字"""
        return any('\u4e00' <= c <= '\u9fff' for c in text)

    def _is_pure_punctuation_or_emoji(self, text: str) -> bool:
        """检查文本是否为纯标点符号或emoji（无实际内容）"""
        for char in text:
            code = ord(char)
            is_emoji = any(start <= code <= end for start, end in EMOJI_RANGES)
            if is_emoji:
                continue
            if char in CHINESE_PUNCTUATION:
                continue
            if char in '.,!?()[]{}":;\'/-_+=*&^%$#@~`':
                continue
            if char.isspace() or ord(char) < 32:
                continue
            return False
        return True

    def _has_cantonese_features(self, text: str) -> bool:
        """严格检测文本是否包含明确的粤语特征

        判定规则：
        - 任意一个词组级特征 OR
        - 任意一个高频单字特征 OR
        - 2个或以上其他单字特征
        """
        if not text or not text.strip():
            return False
        if text.isascii():
            return False
        if not self._has_chinese(text):
            return False

        has_simplified_dian = '点' in text

        # 词组级特征（任意一个即判定为粤语）
        PHRASE_FEATURES = ['點解', '邊度', '做咩', '係咪', '係唔係', '唔該', '多謝', '真係',
                          '你哋', '佢哋', '我哋', '搶飛', '買飛', '點樣', '點算']
        for feature in PHRASE_FEATURES:
            if feature in text:
                return True

        # 高频单字特征（任意一个即可判定）
        STRONG_CHAR_FEATURES = ['冇', '喺', '嘅', '哋', '咁', '咗', '唔', '睇', '俾', '攞',
                                '搵', '咩', '嘞', '乜', '啫', '咖', '喇']
        for char in STRONG_CHAR_FEATURES:
            if char in text:
                return True

        # 其他单字特征（需要至少2个）
        CHAR_FEATURES = ['噉', '吖', '喔', '咯', '噃', '咋', '啩', '啰', '嘎', '㗎']

        if has_simplified_dian:
            return False

        char_count = sum(1 for f in CHAR_FEATURES if f in text)
        return char_count >= 2

    def _is_traditional_chinese(self, text: str) -> bool:
        """使用OpenCC检测文本是简体中文还是繁体中文

        原理：
        - 原文转简体后变化大 → 原文中很多繁体字 → Traditional
        - 原文转繁体后变化大 → 原文中很多简体字 → Simplified
        """
        if not text or not text.strip():
            return False
        if text.isascii() or not self._has_chinese(text):
            return False

        to_simplified = _T2S_CONVERTER.convert(text)
        to_traditional = _S2T_CONVERTER.convert(text)

        diff_s = sum(1 for i in range(len(text))
                    if (i >= len(to_simplified) or text[i] != to_simplified[i]))
        diff_t = sum(1 for i in range(len(text))
                    if (i >= len(to_traditional) or text[i] != to_traditional[i]))

        # 繁体特有字符集合
        TRADITIONAL_SPECIFIC = set('時關閉顯敗賬號場館島龍裏過報簽遞鳥輸優購會員嗎馬罵碼臺們樣點電機話遲礦務國陸內圖數據諮詢證離開單達運資絡網價過錢預賬戶郵詐騙時間麼轉賣買飛會門丟並亞佇佈佔併來係倉個們倫側偵偽傑傘備傳傷僅價儘償優儲兌兒內兩冊凍別刪則剛創剷劃劍動務勢匯區協卻厭參員唄問啟喎單嗎嗰嘗嘩囉國圍圖團報場墮夠夢夾媽嬌學實審寫寵寶將專尋對導層屬峯帥帳帶幣幫幹幾庫廈廢廣廳張強彈後徑從復恆惡愛態慘慮憑應懷戶掃掛採揀換損搖搵搶撐撳擁擇擊擋擔據擠擬擺攜攤攪攬敗數斃斷於時暫書會東條棄業極榮構樂樑樓標樣機檔檢檯檻櫃欄權歐歡歲歸毀氈氣決沒沖況洩淚淨減測準溝溫滅滙滾漢漣潰濤濫瀏灘灣為無煩熱燈爛爾牆狀猶獅獎獨獲現環產畢畫異當發盜盡盤盧眾瞞確碼礙禮種稱穩筆節範簡簽籌籬紀約紅納純紙級細終結絡給統絲綁經綜線維網綴綵緊線編練縮總繫繳繼續罵習聖聯職聽脫腦腳膽臉臨臺與舉舊華萬蓋薦藍藝蘇處虛號螞蟻術衛衝裡補裝裡製複見規視親覺覽觀訂計訊託記請順問設計')

        if diff_s == 0 and diff_t == 0:
            return any(c in TRADITIONAL_SPECIFIC for c in text)

        chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        if chinese_count == 0:
            return False

        change_rate_s = diff_s / chinese_count
        change_rate_t = diff_t / chinese_count

        if change_rate_s < 0.1 and change_rate_t < 0.1:
            count = sum(1 for c in text if c in TRADITIONAL_SPECIFIC)
            return count / chinese_count > 0.3

        diff_diff = diff_s - diff_t

        # 核心逻辑：
        # - diff_s > diff_t: 转为简体需要更多变化，说明原文是繁体
        # - diff_t > diff_s: 转为繁体需要更多变化，说明原文是简体
        # - diff_s == diff_t: 两种转换变化相同，使用TRADITIONAL_SPECIFIC判断

        if diff_diff > 0:  # diff_s > diff_t -> Traditional
            return True
        if diff_diff < 0:  # diff_t > diff_s -> Simplified
            return False

        # diff_s == diff_t 时，使用繁体特有字符比例判断
        count = sum(1 for c in text if c in TRADITIONAL_SPECIFIC)
        if chinese_count > 0:
            return count / chinese_count > 0.3
        return False

    def _detect_chinese_variant(self, text: str) -> Optional[str]:
        """检测中文变体：简体、繁体或粤语

        Returns:
            "Chinese(Simplified)", "Chinese(Traditional)", "Cantonese" or None
        """
        if not text or not text.strip():
            return None
        if text.isascii():
            return None
        if not self._has_chinese(text):
            return None

        stripped = text.strip()

        # 如果包含其他语言字符（非中文），返回None
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
        if self._has_cantonese_features(stripped):
            return "Cantonese"

        # 检测繁体/简体
        if self._is_traditional_chinese(stripped):
            return "Chinese(Traditional)"

        return "Chinese(Simplified)"

    # =========================================================================
    # Text Classification Methods
    # =========================================================================

    def _is_long_text(self, text: str) -> bool:
        """Check if text is long enough to be used for history."""
        stripped = text.strip()
        if stripped.isascii():
            word_count = len(stripped.split())
            return word_count >= 5
        elif any("\u4e00" <= c <= "\u9fff" for c in stripped):
            chinese_count = sum(1 for c in stripped if "\u4e00" <= c <= "\u9fff")
            return chinese_count >= 5
        else:
            return len(stripped) >= 5

    def _is_long_chinese_text(self, text: str) -> bool:
        """判断是否为长中文文本"""
        chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        return chinese_count >= 5

    def _has_strong_chinese_signal(self, text: str) -> bool:
        """判断文本是否有强中文信号"""
        if self._has_cantonese_features(text):
            return True
        if self._is_traditional_chinese(text):
            return True
        return False

    def _has_unicode_signal(self, text: str) -> bool:
        """判断文本是否有强Unicode语言信号（非中文）"""
        if re.search(self.UNICODE_RANGES["Japanese"], text):
            return True
        if re.search(self.UNICODE_RANGES["Korean"], text):
            return True
        if re.search(self.UNICODE_RANGES["Thai"], text):
            return True
        if re.search(self.UNICODE_RANGES["Cyrillic"], text):
            return True
        if re.search(self.UNICODE_RANGES["Arabic"], text):
            return True
        if re.search(self.UNICODE_RANGES["Devanagari"], text):
            return True
        if re.search(self.UNICODE_RANGES["Tamil"], text):
            return True
        if re.search(self.UNICODE_RANGES["Greek"], text):
            return True
        if re.search(self.UNICODE_RANGES["Hebrew"], text):
            return True
        if self._detect_vietnamese(text):
            return True
        return False

    def _is_long_latin_text(self, text: str) -> bool:
        """判断是否为足够长的拉丁文字本（可用于历史参考）"""
        stripped = text.strip()
        if stripped.isascii():
            word_count = len(stripped.split())
            return word_count >= 5
        return len(stripped) >= 10

    def _is_valid_history_text(self, text: str) -> bool:
        """判断文本是否可作为有效历史参考（支持多语言）"""
        # 中文文本
        if self._is_long_chinese_text(text):
            return True
        if self._has_strong_chinese_signal(text):
            return True
        if self._has_chinese(text):
            return True
        # 其他Unicode语言（日韩泰俄等）
        if self._has_unicode_signal(text):
            return True
        # 足够长的拉丁文字本
        if self._is_long_latin_text(text):
            return True
        return False

    def _detect_vietnamese(self, text: str) -> bool:
        """Check if text is likely Vietnamese based on diacritics."""
        diacritic_count = sum(1 for c in text if c in self.VIETNAMESE_DIACRITICS)
        return 'đ' in text.lower() or diacritic_count >= self.VIETNAMESE_MIN_DIACRITICS

    def _detect_by_unicode(self, text: str) -> Optional[str]:
        """Detect language by Unicode character ranges (non-Chinese)."""
        if not text or not text.strip():
            return None

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
        if self._detect_vietnamese(text):
            return "Vietnamese"

        return None

    def _build_lingua_detector(self):
        """Build lingua detector with 6 languages."""
        return LanguageDetectorBuilder.from_languages(
            Language.ENGLISH,
            Language.FRENCH,
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

    # 常见英文单词（短文本容易误判）
    COMMON_ENGLISH_WORDS = {
        "hello", "hi", "hey", "yes", "no", "ok", "okay",
        "good", "great", "nice", "well", "fine", "bad",
        "thank", "thanks", "sorry", "please", "help",
        "love", "like", "want", "need", "know", "think",
        "make", "take", "come", "here", "there", "where",
        "what", "when", "why", "how", "who", "which",
        "this", "that", "these", "those", "it", "is", "are",
        "was", "were", "been", "have", "has", "had",
        "do", "does", "did", "will", "would", "could", "should",
        "can", "may", "might", "must", "shall",
        "i", "me", "my", "we", "us", "our", "you", "your",
        "he", "she", "him", "her", "his", "they", "them", "their",
        "the", "a", "an", "of", "in", "to", "for", "on", "at",
        "by", "with", "from", "or", "and", "but", "if", "not",
        "up", "down", "out", "over", "under", "again", "more",
        "all", "any", "some", "most", "other", "such", "only",
        "same", "so", "than", "too", "very", "just", "now",
        "then", "also", "back", "about", "after", "before",
        "world", "text", "test", "code", "file", "data",
        "name", "time", "way", "day", "year", "work", "thing",
        "people", "child", "man", "woman", "see", "look", "get",
        "use", "find", "give", "tell", "ask", "try", "call",
        "keep", "let", "put", "show", "hear", "play", "run",
        "move", "live", "believe", "hold", "bring", "happen",
        "write", "provide", "sit", "stand", "lose", "pay",
        "meet", "include", "continue", "set", "learn", "change",
        "lead", "understand", "watch", "follow", "stop", "create",
        "speak", "read", "spend", "grow", "open", "walk", "win",
        "offer", "remember", "love", "consider", "appear", "buy",
        "wait", "serve", "die", "send", "expect", "build", "stay",
        "fall", "cut", "reach", "kill", "remain", "suggest", "raise",
    }

    def _detect_base(self, text: str) -> str:
        """Base detection without history."""
        if not text or not text.strip():
            return "English"

        text = text.strip()
        text_lower = text.lower()

        # 首先尝试中文变体检测（使用OpenCC）
        chinese_variant = self._detect_chinese_variant(text)
        if chinese_variant:
            return chinese_variant

        # 然后尝试其他Unicode语言
        unicode_lang = self._detect_by_unicode(text)
        if unicode_lang:
            return unicode_lang

        # 短文本特殊处理：常见英文单词直接返回English
        if len(text) <= 5 and text_lower in self.COMMON_ENGLISH_WORDS:
            return "English"

        # 最后用lingua检测Latin语言
        try:
            detector = self._get_lingua_detector()
            result = detector.detect_language_of(text)
            if result:
                # 短文本结果特殊处理
                if len(text) <= 10 and result == Language.SPANISH and text_lower in self.COMMON_ENGLISH_WORDS:
                    return "English"
                return self.LINGUA_LANG_MAP.get(result, "English")
        except Exception:
            pass

        return "English"

    def detect(self, text: str, history: Optional[list[str]] = None) -> str:
        """
        Detect language of the given text.

        Args:
            text: Input text to detect language for.
            history: Optional list of previous texts to help determine
                    language for short ambiguous texts.

        Returns:
            Language name as string, e.g.:
            - "Chinese(Simplified)", "Chinese(Traditional)", "Cantonese"
            - "Japanese", "Korean", "Thai", "Russian", etc.
            - "English", "Malay", "Spanish", "Portuguese", "Indonesian"
        """
        if not text or not text.strip():
            return "English"

        stripped = text.strip()

        # 检查是否纯数字（电话号码、日期等）
        is_pure_number = bool(
            re.match(r'^[\d\-\.\s\(\)]+$', stripped) and
            stripped.replace('-', '').replace('.', '').replace(' ', '').replace('(', '').replace(')', '').isdigit()
        )

        # 检查是否ASCII或纯标点/emoji
        is_ascii_only = stripped.isascii()
        is_pure_punct_emoji = self._is_pure_punctuation_or_emoji(stripped)

        # 短文本或纯emoji/标点文本，如果有历史则使用历史判断
        text_is_short_or_pure = (
            not self._is_long_text(text) or
            is_pure_number or
            (is_ascii_only and is_pure_punct_emoji) or
            is_pure_punct_emoji
        )
        should_use_history = bool(text_is_short_or_pure) and history

        if should_use_history:
            hist_lang_counts: dict[str, int] = {}
            for hist_text in history or []:
                hist_normalized = self._normalize_text(hist_text)
                if self._is_valid_history_text(hist_normalized):
                    hist_result = self._detect_base(hist_normalized)
                    hist_lang_counts[hist_result] = hist_lang_counts.get(hist_result, 0) + 1

            # 找到出现最多的语言
            if hist_lang_counts:
                total = sum(hist_lang_counts.values())
                dominant_lang = max(hist_lang_counts, key=lambda k: hist_lang_counts[k])
                ratio = hist_lang_counts[dominant_lang] / total

                # 历史判断逻辑：
                # - 至少需要4条有效历史记录，且
                # - dominant语言比例超过70%
                # - 但如果只有1条历史且是100%中文，短文本也应该采纳
                if total >= 4 and ratio >= 0.7:
                    return dominant_lang
                # 只有1条历史记录时，如果是100%同一种语言，短文本采纳
                if total == 1 and ratio == 1.0:
                    return dominant_lang

        return self._detect_base(text)


# =============================================================================
# Convenience Function
# =============================================================================

def detect_language(text: str, history: Optional[list[str]] = None) -> str:
    """
    Detect language of the given text (convenience function).

    Args:
        text: Input text to detect language for.
        history: Optional list of previous texts to help determine
                language for short ambiguous texts.

    Returns:
        Language name as string.
    """
    detector = LanguageDetector()
    return detector.detect(text, history)


# =============================================================================
# Main Test
# =============================================================================

if __name__ == "__main__":
    detector = LanguageDetector()

    # ============================================================
    # 测试用例 - 基础检测
    # ============================================================
    print("=" * 70)
    print("PART 1: Basic Language Detection Tests")
    print("=" * 70)

    basic_tests = [
        # 中文简体
        ("你好，世界", "Chinese(Simplified)"),
        ("今天天气真好", "Chinese(Simplified)"),
        ("最新有哪些活动", "Chinese(Simplified)"),
        ("最近有哪些演出门票开售？", "Chinese(Simplified)"),
        ("我的门票有哪些", "Chinese(Simplified)"),
        # 中文繁体
        ("愛台灣", "Chinese(Traditional)"),
        ("時間", "Chinese(Traditional)"),
        ("網絡", "Chinese(Traditional)"),
        ("請問位置是按付款順序嗎", "Chinese(Traditional)"),
        ("門票會有什麼方式送到？", "Chinese(Traditional)"),
        # 粤语
        ("點解唔係啊", "Cantonese"),
        ("你哋做咩啊", "Cantonese"),
        ("我的帳戶給朋友幫我搶飛", "Cantonese"),
        ("支付寶可唔可以俾錢？", "Cantonese"),
        # 日语
        ("こんにちは", "Japanese"),
        ("ありがとう", "Japanese"),
        # 韩语
        ("안녕하세요", "Korean"),
        ("멤버십 등록", "Korean"),
        # 泰语
        ("สวัสดีครับ", "Thai"),
        ("พอถึงเวลากดบัตรต้องกดรีเฟรชอีกมีไหม", "Thai"),
        # 俄语
        ("Привет мир", "Russian"),
        ("Сколько рядов там будет", "Russian"),
        # 阿拉伯语
        ("مرحبا", "Arabic"),
        # 印地语
        ("नमस्ते", "Hindi"),
        # 泰米尔语
        ("வணக்கம்", "Tamil"),
        # 英语
        ("Hello world", "English"),
        ("How about member presale by using one pay click", "English"),
        # 西班牙语
        ("Hola mundo", "Spanish"),
        ("¿Qué métodos de pago se admiten?", "Spanish"),
        # 葡萄牙语
        ("Olá mundo", "Portuguese"),
        # 马来语
        ("Malaysia adalah negara yang indah", "Malay"),
        # 印尼语
        ("Indonesia adalah negara kepulauan", "Indonesian"),
    ]

    all_passed = True
    for text, expected in basic_tests:
        result = detector.detect(text)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"{status} {text[:40]:40} -> {result:25} (expected: {expected})")

    print(f"\n{'✓ All basic tests passed!' if all_passed else '✗ Some basic tests failed!'}")

    # ============================================================
    # 测试用例 - 真实数据样本
    # ============================================================
    print("\n" + "=" * 70)
    print("PART 2: Real Data Samples from result2.csv")
    print("=" * 70)

    real_data_tests = [
        # 繁体中文 - 真实用户输入
        ("你好，想問一下地址能填順豐櫃的地址嗎？", "Chinese(Traditional)"),
        ("是不是我搶到票之後能決定要郵寄還是演出當天來拿票？", "Chinese(Traditional)"),
        ("用AlipayHK在購買演唱會門票可以不綁定銀行卡嗎", "Chinese(Traditional)"),
        # 粤语 - 真实用户输入
        ("点解。一入去riize就冇票", "Cantonese"),
        ("點解入會員號碼話錯誤？我係跟官網copy咖喎", "Cantonese"),
        ("iPad算唔算電腦？可唔可以搶飛？", "Cantonese"),
        # 英语 - 真实用户输入
        ("Hi I am mango .I like to visit Macao", "English"),
        ("Is it better to use a PC or the mobile app when purchasing tickets?", "English"),
        ("What is offline ticket redemption?", "English"),
        # 泰语 - 真实用户输入
        ("มีคำถามฝ่ายบริการลูกค้า", "Thai"),
        ("อยากรุ้ที่นั่งแล้วอ่า", "Thai"),
        # 韩语 - 真实用户输入
        ("표를 취소하고 다시 예매하고싶어요", "Korean"),
        ("카드결제만 환불되고 이메일은 오지않았어", "Korean"),
        # 俄语 - 真实用户输入
        ("Там написано что у меня вип сектор Row B4 seat 31 что это значит?", "Russian"),
        # 日语 - 真实用户输入
        ("パクボゴム", "Japanese"),
        ("waitlistをキャンセルしたい", "Japanese"),
        # 西班牙语 - 真实用户输入
        ("¿Cómo puedo contactar con atención al cliente?", "Spanish"),
        # 越南语 - 真实用户输入
        ("Tôi vẫn chưa nhận được số queue", "Vietnamese"),
    ]

    all_passed = True
    for text, expected in real_data_tests:
        result = detector.detect(text)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"{status} {text[:40]:40} -> {result:25} (expected: {expected})")

    print(f"\n{'✓ All real data tests passed!' if all_passed else '✗ Some real data tests failed!'}")

    # ============================================================
    # 测试用例 - 历史推断
    # ============================================================
    print("\n" + "=" * 70)
    print("PART 3: History-based Language Detection")
    print("=" * 70)

    history_tests = [
        # 短文本 + 中文历史 -> 推断为中文
        ("ok", ["今天天气真好"], "Chinese(Simplified)"),
        ("好", ["最新有哪些活动"], "Chinese(Simplified)"),
        ("好", ["請問位置是按付款順序嗎"], "Chinese(Traditional)"),
        # 短文本 + 粤语历史 -> 推断为粤语
        ("ok", ["點解唔係啊"], "Cantonese"),
        ("好", ["iPad算唔算電腦？可唔可以搶飛？"], "Cantonese"),
        # 短文本 + 强语言历史 -> 推断为该语言
        # 注意：英文不在 STRONG_LANGUAGES 中，所以英文历史无法帮助推断
        # 无历史 - 可能被误判
        ("ok", None, "Indonesian"),  # 已知问题：ok会被识别为印尼语
    ]

    all_passed = True
    for text, history, expected in history_tests:
        result = detector.detect(text, history)
        status = "✓" if result == expected else "✗"
        history_str = str(history)[:30] if history else "None"
        if result != expected:
            all_passed = False
        print(f"{status} text='{text:10}' history={history_str:35} -> {result:20} (expected: {expected})")

    print(f"\n{'✓ All history tests passed!' if all_passed else '✗ Some history tests failed!'}")

    # ============================================================
    # 测试用例 - 短文本和边界情况
    # ============================================================
    print("\n" + "=" * 70)
    print("PART 4: Short Text and Edge Cases")
    print("=" * 70)

    edge_tests = [
        # 纯数字
        ("123123123", "English"),  # 纯数字默认英文
        ("123-456-789", "English"),
        # 纯标点/emoji
        ("哈哈哈", "Chinese(Simplified)"),  # 笑声是中文
        ("???", "English"),
        # 单字符
        ("好", "Chinese(Simplified)"),
        # 短ASCII词会被lingua识别为马来语（已知行为）
        ("a", "Malay"),
        # 混合场景 - 包含汉字则优先判断为中文
        ("I like 你好", "Chinese(Simplified)"),
        # 短英文词会被lingua识别为马来语/印尼语
        ("ok google", "Indonesian"),
    ]

    all_passed = True
    for text, expected in edge_tests:
        result = detector.detect(text)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"{status} {text[:30]:30} -> {result:25} (expected: {expected})")

    print(f"\n{'✓ All edge case tests passed!' if all_passed else '✗ Some edge case tests failed!'}")

    print("\n" + "=" * 70)
    print("All Test Suites Complete!")
    print("=" * 70)
