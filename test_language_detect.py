"""测试 language_detect.py 模块

使用 result2.csv 中的数据验证语言检测准确性。
"""

import csv
from collections import defaultdict
from language_detect import detect_language


def run_tests(input_file: str, sample_size: int = 5000):
    """运行测试

    Args:
        input_file: 测试数据文件路径
        sample_size: 随机抽样的测试样本数量
    """
    # 读取数据
    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"加载数据: {len(rows)} 条")

    # 随机抽样测试
    import random
    random.seed(42)
    sample = random.sample(rows, min(sample_size, len(rows)))

    # 统计
    stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'mismatches': []})

    for row in sample:
        content = row['content']
        expected = row['language']
        detected = detect_language(content)

        key = expected
        stats[key]['total'] += 1

        if detected == expected:
            stats[key]['correct'] += 1
        else:
            # 记录错配
            if len(stats[key]['mismatches']) < 3:  # 每个语言最多记录3个
                stats[key]['mismatches'].append({
                    'expected': expected,
                    'detected': detected,
                    'content': content[:80]
                })

    # 输出结果
    print("\n" + "=" * 70)
    print("测试结果")
    print("=" * 70)

    total_correct = sum(v['correct'] for v in stats.values())
    total_tests = sum(v['total'] for v in stats.values())
    overall_accuracy = total_correct / total_tests * 100 if total_tests > 0 else 0

    print(f"\n总体准确率: {overall_accuracy:.2f}% ({total_correct}/{total_tests})")

    print("\n各语言准确率:")
    print("-" * 70)
    print(f"{'语言':25s} {'准确率':>10s} {'正确/总数':>15s}")
    print("-" * 70)

    for lang in sorted(stats.keys(), key=lambda x: -stats[x]['total']):
        data = stats[lang]
        accuracy = data['correct'] / data['total'] * 100 if data['total'] > 0 else 0
        print(f"{lang:25s} {accuracy:>9.1f}% {data['correct']:>6d}/{data['total']:<6d}")

    # 显示错配样例
    print("\n" + "=" * 70)
    print("错配样例（每个语言最多显示3个）")
    print("=" * 70)

    has_mismatches = False
    for lang in sorted(stats.keys(), key=lambda x: -stats[x]['total']):
        if stats[lang]['mismatches']:
            has_mismatches = True
            print(f"\n[{lang}]")
            for m in stats[lang]['mismatches']:
                print(f"  期望: {m['expected']:20s} -> 检测: {str(m['detected']):20s}")
                print(f"  文本: {m['content']}")

    if not has_mismatches:
        print("\n所有样本检测正确！")

    # 返回总体准确率
    return overall_accuracy


def full_test(input_file: str):
    """完整测试所有数据（较慢）"""
    print("运行完整测试...")

    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"测试数据: {len(rows)} 条")

    total_correct = 0
    total_tests = 0
    mismatches = defaultdict(list)

    for i, row in enumerate(rows):
        if i % 10000 == 0:
            print(f"进度: {i}/{len(rows)}")

        content = row['content']
        expected = row['language']
        detected = detect_language(content)

        total_tests += 1
        if detected == expected:
            total_correct += 1
        else:
            key = expected
            if len(mismatches[key]) < 2:
                mismatches[key].append((expected, detected, content[:80]))

    accuracy = total_correct / total_tests * 100 if total_tests > 0 else 0
    print(f"\n总体准确率: {accuracy:.2f}% ({total_correct}/{total_tests})")

    if mismatches:
        print("\n错配样例:")
        for lang, items in sorted(mismatches.items()):
            print(f"\n[{lang}]")
            for expected, detected, content in items:
                print(f"  期望: {expected} -> 检测: {detected}")
                print(f"  文本: {content}")

    return accuracy


if __name__ == '__main__':
    import sys

    input_file = 'result2.csv'

    if '--full' in sys.argv:
        full_test(input_file)
    else:
        run_tests(input_file, sample_size=5000)
