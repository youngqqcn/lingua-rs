"""数据清洗脚本

清洗 result2.csv 中的异常文本：
1. 过滤 <=3 字符的 English 短文本
2. K-pop/J-pop 团体名称重新分类为 Chinese(Simplified)
3. 包含中文关键词的英文文本重新分类为 Chinese(Simplified)
"""

import csv
import re

# =============================================================================
# 常量定义
# =============================================================================

# 过滤阈值
SHORT_TEXT_MAX_LEN = 3  # <= 3 字符的 English 文本过滤

# K-pop/J-pop 团体名称黑名单（统一小写存储，匹配时转小写）
KPOP_GROUPS = [
    'blackpink', 'bp', 'exo', 'twice', 'nct', 'nctwish', 'bts', 'riize', 'rii ze', 'riizing',
    'aespa', 'ive', 'newjeans', 'enhypen', 'seventeen', 'txt', 'tws',
    'super junior', 'red velvet', 'the boyz', 'babymonster', 'lesserafim',
    'itzy', 'ateez', 'kep1er', 'mamamoo', 'oneus', 'stray kids',
    'andteam', 'monsta x', '(g)i-dle', 'black pink',
]

# 过滤模式
PURE_NUMBER_PATTERN = re.compile(r'^\d{5,}$')  # 5位以上纯数字
BOOKING_CODE_PATTERN = re.compile(r'^(RB|BC|PC|TC)\d+$', re.IGNORECASE)  # 预订代码

# 中文关键词（存在则说明是中文句子被误识为英文）
CHINESE_KEYWORDS = ['演唱会', '门票', '在哪里', '什么时候', '粉丝', '位置', '座位', '香港', '澳门']


# =============================================================================
# 检测函数
# =============================================================================

def is_kpop(text):
    """检测是否包含K-pop团体名称"""
    text_lower = text.lower()
    for group in KPOP_GROUPS:
        if group in text_lower:
            return True
    return False


def has_chinese_keywords(text):
    """检测是否包含中文关键词"""
    for keyword in CHINESE_KEYWORDS:
        if keyword in text:
            return True
    return False


def should_filter(text, lang):
    """判断文本是否需要过滤或重新分类

    Returns:
        (should_filter: bool, new_lang: str | None)
        - should_filter=True: 过滤该文本
        - new_lang != None: 重新分类为指定语言
    """
    # 仅处理 English
    if lang != 'English':
        return False, lang  # 返回原语言

    # 1. 短文本过滤
    if len(text.strip()) <= SHORT_TEXT_MAX_LEN:
        return True, None  # 过滤

    # 2. 纯数字过滤
    if PURE_NUMBER_PATTERN.match(text.strip()):
        return True, None

    # 3. Booking code 过滤
    if BOOKING_CODE_PATTERN.match(text.strip()):
        return True, None

    # 4. K-pop团体名称 → 重新分类为 Chinese(Simplified)
    if is_kpop(text):
        return False, 'Chinese(Simplified)'

    # 5. 包含中文关键词 → 重新分类为 Chinese(Simplified)
    if has_chinese_keywords(text):
        return False, 'Chinese(Simplified)'

    return False, lang  # 保留原分类


# =============================================================================
# 主函数
# =============================================================================

def main():
    input_file = "result2.csv"
    output_file = "result2.csv"  # 覆盖原文件

    stats = {
        'total': 0,
        'filtered': 0,
        'reclassified': 0,
        'reclassifications': {},  # {(old_lang, new_lang): count}
    }

    rows = []
    with open(input_file, "r", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        for row in reader:
            stats['total'] += 1
            content = row["content"]
            language = row["language"]

            should_filter_flag, new_lang = should_filter(content, language)

            if should_filter_flag:
                stats['filtered'] += 1
            elif new_lang != language:
                stats['reclassified'] += 1
                key = (language, new_lang)
                stats['reclassifications'][key] = stats['reclassifications'].get(key, 0) + 1
                row["language"] = new_lang
                rows.append(row)
            else:
                rows.append(row)

    # 写入 result2.csv（覆盖）
    with open(output_file, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["user_id", "content", "language"])
        writer.writeheader()
        writer.writerows(rows)

    # 重新生成 statistic.csv
    from collections import defaultdict
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
    print("数据清洗完成")
    print("=" * 50)
    print(f"总记录数: {stats['total']}")
    print(f"被过滤: {stats['filtered']}")
    print(f"被重新分类: {stats['reclassified']}")
    print(f"有效记录: {len(rows)}")
    if stats['reclassifications']:
        print(f"\n重新分类明细:")
        for (old_lang, new_lang), count in stats['reclassifications'].items():
            print(f"  {old_lang} → {new_lang}: {count}")
    print(f"\nresult2.csv 和 statistic.csv 已更新")


if __name__ == "__main__":
    main()