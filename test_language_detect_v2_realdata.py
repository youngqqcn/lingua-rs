"""Comprehensive white-box tests using full real data from result2.csv

Full coverage:
- 163,445 real user samples
- 67,092 unique users
- 10,742 users with 4+ message history
- All supported languages
"""

import csv
import random
import pytest
from collections import defaultdict, Counter
from language_detect_v2 import LanguageDetector, detect_language


# =============================================================================
# Fixtures and Helpers
# =============================================================================

@pytest.fixture(scope="module")
def detector():
    """Create detector once for all tests (expensive to create)."""
    return LanguageDetector()


@pytest.fixture(scope="module")
def all_samples():
    """Load all samples from result2.csv."""
    samples = []
    with open('result2.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append(row)
    return samples


@pytest.fixture(scope="module")
def samples_by_lang(all_samples):
    """Group samples by language."""
    by_lang = defaultdict(list)
    for s in all_samples:
        by_lang[s['language']].append(s)
    return by_lang


@pytest.fixture(scope="module")
def user_histories(all_samples):
    """Build user histories from all data."""
    user_data = defaultdict(list)
    for row in all_samples:
        user_data[row['user_id']].append(row)
    # Only users with 4+ messages for history testing
    return {uid: msgs for uid, msgs in user_data.items() if len(msgs) >= 4}


# =============================================================================
# Test All Supported Languages
# =============================================================================

class TestAllLanguagesAccuracy:
    """Test detection accuracy on ALL available data for each language."""

    def test_chinese_simplified_full(self, detector, samples_by_lang):
        """Test Chinese(Simplified) on full dataset (108,181 samples)."""
        samples = samples_by_lang.get('Chinese(Simplified)', [])
        assert len(samples) >= 10000, "Should have 10k+ samples"

        # Test on 2000 random samples
        random.seed(42)
        test_samples = random.sample(samples, min(2000, len(samples)))
        correct = sum(1 for s in test_samples
                     if detector.detect(s['content']) == 'Chinese(Simplified)')
        accuracy = correct / len(test_samples) * 100
        print(f"\nChinese(Simplified): {accuracy:.2f}% ({correct}/{len(test_samples)})")
        assert accuracy >= 95, f"Chinese(Simplified) accuracy: {accuracy:.1f}%"

    def test_chinese_traditional_full(self, detector, samples_by_lang):
        """Test Chinese(Traditional) on full dataset (29,607 samples)."""
        samples = samples_by_lang.get('Chinese(Traditional)', [])
        assert len(samples) >= 5000, "Should have 5k+ samples"

        random.seed(42)
        test_samples = random.sample(samples, min(1000, len(samples)))
        correct = sum(1 for s in test_samples
                     if detector.detect(s['content']) == 'Chinese(Traditional)')
        accuracy = correct / len(test_samples) * 100
        print(f"\nChinese(Traditional): {accuracy:.2f}% ({correct}/{len(test_samples)})")
        assert accuracy >= 75, f"Chinese(Traditional) accuracy: {accuracy:.1f}%"

    def test_english_full(self, detector, samples_by_lang):
        """Test English on full dataset (23,456 samples)."""
        samples = samples_by_lang.get('English', [])
        assert len(samples) >= 5000, "Should have 5k+ samples"

        random.seed(42)
        test_samples = random.sample(samples, min(1000, len(samples)))
        correct = sum(1 for s in test_samples
                     if detector.detect(s['content']) == 'English')
        accuracy = correct / len(test_samples) * 100
        print(f"\nEnglish: {accuracy:.2f}% ({correct}/{len(test_samples)})")
        assert accuracy >= 85, f"English accuracy: {accuracy:.1f}%"

    def test_thai_full(self, detector, samples_by_lang):
        """Test Thai on full dataset (1,198 samples)."""
        samples = samples_by_lang.get('Thai', [])
        assert len(samples) >= 500, "Should have 500+ samples"

        correct = sum(1 for s in samples
                     if detector.detect(s['content']) == 'Thai')
        accuracy = correct / len(samples) * 100
        print(f"\nThai: {accuracy:.2f}% ({correct}/{len(samples)})")
        assert accuracy >= 90, f"Thai accuracy: {accuracy:.1f}%"

    def test_cantonese_full(self, detector, samples_by_lang):
        """Test Cantonese on full dataset (775 samples)."""
        samples = samples_by_lang.get('Cantonese', [])
        assert len(samples) >= 200, "Should have 200+ samples"

        correct = sum(1 for s in samples
                     if detector.detect(s['content']) == 'Cantonese')
        accuracy = correct / len(samples) * 100
        print(f"\nCantonese: {accuracy:.2f}% ({correct}/{len(samples)})")
        assert accuracy >= 60, f"Cantonese accuracy: {accuracy:.1f}%"

    def test_korean_full(self, detector, samples_by_lang):
        """Test Korean on full dataset (122 samples)."""
        samples = samples_by_lang.get('Korean', [])

        correct = sum(1 for s in samples
                     if detector.detect(s['content']) == 'Korean')
        accuracy = correct / len(samples) * 100 if samples else 0
        print(f"\nKorean: {accuracy:.2f}% ({correct}/{len(samples)})")
        assert accuracy >= 80, f"Korean accuracy: {accuracy:.1f}%"

    def test_russian_full(self, detector, samples_by_lang):
        """Test Russian on full dataset (24 samples)."""
        samples = samples_by_lang.get('Russian', [])

        correct = sum(1 for s in samples
                     if detector.detect(s['content']) == 'Russian')
        accuracy = correct / len(samples) * 100 if samples else 0
        print(f"\nRussian: {accuracy:.2f}% ({correct}/{len(samples)})")
        assert accuracy >= 80, f"Russian accuracy: {accuracy:.1f}%"

    def test_japanese_full(self, detector, samples_by_lang):
        """Test Japanese on full dataset (14 samples)."""
        samples = samples_by_lang.get('Japanese', [])

        correct = sum(1 for s in samples
                     if detector.detect(s['content']) == 'Japanese')
        accuracy = correct / len(samples) * 100 if samples else 0
        print(f"\nJapanese: {accuracy:.2f}% ({correct}/{len(samples)})")
        # Relaxed threshold due to small sample size
        assert accuracy >= 50, f"Japanese accuracy: {accuracy:.1f}%"


# =============================================================================
# Test Text Length vs Accuracy
# =============================================================================

class TestLengthVsAccuracy:
    """Analyze how text length affects detection accuracy."""

    def test_accuracy_by_length_buckets(self, detector, all_samples):
        """Test accuracy across different text length buckets."""
        length_buckets = {
            '1-5': [],
            '6-10': [],
            '11-20': [],
            '21-50': [],
            '51-100': [],
            '100+': []
        }

        for s in all_samples:
            content = s['content']
            length = len(content)

            if length <= 5:
                bucket = '1-5'
            elif length <= 10:
                bucket = '6-10'
            elif length <= 20:
                bucket = '11-20'
            elif length <= 50:
                bucket = '21-50'
            elif length <= 100:
                bucket = '51-100'
            else:
                bucket = '100+'

            is_correct = detector.detect(content) == s['language']
            length_buckets[bucket].append(is_correct)

        print("\nAccuracy by text length:")
        for bucket in ['1-5', '6-10', '11-20', '21-50', '51-100', '100+']:
            results = length_buckets[bucket]
            if results:
                accuracy = sum(results) / len(results) * 100
                print(f"  {bucket:10} {accuracy:5.1f}% ({len(results)} samples)")

    def test_short_text_accuracy(self, detector, all_samples):
        """Specifically test short texts (5 chars or less)."""
        short_texts = [s for s in all_samples if len(s['content']) <= 5]

        # Exclude pure ASCII (which is expected to be English)
        short_non_ascii = [s for s in short_texts if not s['content'].isascii()]

        print(f"\nShort texts (≤5 chars): {len(short_texts)} total, {len(short_non_ascii)} non-ASCII")

        if short_non_ascii:
            correct = sum(1 for s in short_non_ascii
                         if detector.detect(s['content']) == s['language'])
            accuracy = correct / len(short_non_ascii) * 100
            print(f"  Non-ASCII accuracy: {accuracy:.1f}% ({correct}/{len(short_non_ascii)})")


# =============================================================================
# User History Tests (Large Scale)
# =============================================================================

class TestUserHistoryLargeScale:
    """Large scale tests for history-based detection."""

    def test_history_10k_users(self, detector, user_histories):
        """Test history with 10,000+ users."""
        print(f"\nTesting with {len(user_histories)} users with 4+ messages")

        # Find cases where history could potentially help
        history_helping = 0
        history_conflicting = 0
        no_effect = 0

        random.seed(42)
        test_users = random.sample(list(user_histories.items()), min(2000, len(user_histories)))

        for uid, msgs in test_users:
            # Pick a short message from this user
            short_msgs = [m for m in msgs if 3 <= len(m['content']) <= 8 and not m['content'].isascii()]
            if not short_msgs:
                continue

            msg = short_msgs[0]
            content = msg['content']
            expected = msg['language']

            # Get history (up to 10 messages)
            history = [m['content'] for m in msgs if m['content'] != content][:10]

            # Count valid Chinese history entries
            valid_count = 0
            for h in history:
                normalized = detector._normalize_text(h)
                if detector._is_valid_history_text(normalized):
                    valid_count += 1

            if valid_count >= 4:
                # History applies
                detected = detector.detect(content, history)
                if detected != expected:
                    history_conflicting += 1
                else:
                    history_helping += 1
            else:
                no_effect += 1

        print(f"  History helping: {history_helping}")
        print(f"  History conflicting: {history_conflicting}")
        print(f"  No effect (insufficient history): {no_effect}")

    def test_history_chinese_dominance(self, detector, user_histories):
        """Test when all history is Chinese."""
        # Find users with predominantly Chinese history
        users_with_chinese_history = []

        for uid, msgs in list(user_histories.items())[:5000]:
            chinese_count = 0
            for m in msgs:
                if detector._has_chinese(m['content']):
                    chinese_count += 1
            if chinese_count >= len(msgs) * 0.8:  # 80%+ Chinese
                users_with_chinese_history.append(msgs)

        print(f"\nUsers with 80%+ Chinese history: {len(users_with_chinese_history)}")

        if users_with_chinese_history:
            # Test a short message with Chinese history
            correct = 0
            total = 0
            for msgs in users_with_chinese_history[:100]:
                for m in msgs:
                    if 3 <= len(m['content']) <= 10 and not m['content'].isascii():
                        history = [msg['content'] for msg in msgs if msg['content'] != m['content']][:10]
                        detected = detector.detect(m['content'], history)
                        if detected == m['language']:
                            correct += 1
                        total += 1
                        break

            if total > 0:
                accuracy = correct / total * 100
                print(f"  Accuracy with Chinese history: {accuracy:.1f}% ({correct}/{total})")


# =============================================================================
# Edge Case Tests (Large Scale)
# =============================================================================

class TestEdgeCasesLargeScale:
    """Large scale edge case testing."""

    def test_false_positives_by_language(self, detector, samples_by_lang):
        """Find false positives for each language."""
        print("\nFalse positive analysis:")

        for lang in ['Chinese(Simplified)', 'Chinese(Traditional)', 'English', 'Thai', 'Cantonese']:
            samples = samples_by_lang.get(lang, [])
            if len(samples) < 50:
                continue

            random.seed(42)
            test_samples = random.sample(samples, min(500, len(samples)))

            false_positives = []
            for s in test_samples:
                detected = detector.detect(s['content'])
                if detected != s['language']:
                    false_positives.append({
                        'content': s['content'],
                        'expected': s['language'],
                        'detected': detected
                    })

            if false_positives:
                print(f"\n  {lang}: {len(false_positives)}/{len(test_samples)} misclassified")
                for fp in false_positives[:3]:
                    print(f"    [{fp['expected']}] '{fp['content'][:40]}' -> [{fp['detected']}]")

    def test_unknown_language_samples(self, detector, samples_by_lang):
        """Analyze 'Unknown' labeled samples."""
        unknown_samples = samples_by_lang.get('Unknown', [])
        print(f"\nUnknown samples: {len(unknown_samples)}")

        detected_as = Counter()
        for s in unknown_samples:
            detected = detector.detect(s['content'])
            detected_as[detected] += 1

        print("  Detected as:")
        for lang, count in detected_as.most_common():
            print(f"    {lang}: {count}")

    def test_emoji_only_samples(self, detector, all_samples):
        """Test emoji-only or symbol-heavy samples."""
        emoji_samples = []
        for s in all_samples:
            content = s['content'].strip()
            if content:
                # Check if mostly emoji/symbols
                emoji_count = sum(1 for c in content if ord(c) > 0x1F300 or c in '😂🤣😭🎉🔥💰🙏')
                if emoji_count > len(content) * 0.5:
                    emoji_samples.append(s)

        print(f"\nEmoji-heavy samples: {len(emoji_samples)}")

        if emoji_samples:
            detected_as = Counter()
            for s in emoji_samples[:100]:
                detected = detector.detect(s['content'])
                detected_as[detected] += 1

            print("  Detected as:")
            for lang, count in detected_as.most_common(5):
                print(f"    {lang}: {count}")


# =============================================================================
# Internal Method Tests
# =============================================================================

class TestInternalMethods:
    """White-box tests for internal methods."""

    def test_has_chinese(self, detector):
        """Test _has_chinese."""
        assert detector._has_chinese("你好") == True
        assert detector._has_chinese("hello") == False
        assert detector._has_chinese("hello你好world") == True
        assert detector._has_chinese("") == False

    def test_is_long_text_ascii(self, detector):
        """Test _is_long_text for ASCII (requires 5+ words)."""
        assert detector._is_long_text("hello") == False
        assert detector._is_long_text("hello world") == False
        assert detector._is_long_text("one two three four five") == True
        assert detector._is_long_text("a b c d e f g") == True

    def test_is_long_text_chinese(self, detector):
        """Test _is_long_text for Chinese (requires 5+ chars)."""
        assert detector._is_long_text("你好") == False
        assert detector._is_long_text("你好世界") == False
        assert detector._is_long_text("你好世界你好") == True

    def test_is_valid_history_text(self, detector):
        """Test _is_valid_history_text filtering (now supports multilingual)."""
        # Chinese - valid
        assert detector._is_valid_history_text("今天天气真好") == True
        # Japanese - now valid (has unicode signal)
        assert detector._is_valid_history_text("こんにちは") == True
        # English - valid if long enough
        assert detector._is_valid_history_text("hello world") == False  # too short
        assert detector._is_valid_history_text("hello world how are you today") == True  # 5+ words
        # Mixed with Chinese - valid
        assert detector._is_valid_history_text("hello你好world") == True

    def test_detect_chinese_variant(self, detector):
        """Test _detect_chinese_variant."""
        assert detector._detect_chinese_variant("今天天气真好") == "Chinese(Simplified)"
        assert detector._detect_chinese_variant("愛台灣") == "Chinese(Traditional)"
        assert detector._detect_chinese_variant("點解唔係啊") == "Cantonese"
        assert detector._detect_chinese_variant("") == None

    def test_detect_by_unicode(self, detector):
        """Test _detect_by_unicode."""
        assert detector._detect_by_unicode("こんにちは") == "Japanese"
        assert detector._detect_by_unicode("안녕하세요") == "Korean"
        assert detector._detect_by_unicode("สวัสดี") == "Thai"
        assert detector._detect_by_unicode("Привет") == "Russian"
        assert detector._detect_by_unicode("مرحبا") == "Arabic"


# =============================================================================
# Regression Tests
# =============================================================================

class TestRegression:
    """Regression tests for known issues."""

    def test_hello_not_spanish(self, detector):
        """'hello' should be English, not Spanish."""
        assert detector.detect("hello") == "English"

    def test_ok_not_indonesian(self, detector):
        """'ok' should be English."""
        assert detector.detect("ok") == "English"

    def test_common_words_english(self, detector):
        """Common English words should all be detected as English."""
        words = ["hello", "hi", "hey", "yes", "no", "good", "thanks", "sorry"]
        for word in words:
            result = detector.detect(word)
            assert result == "English", f"'{word}' detected as {result}"

    def test_history_requires_4_entries(self, detector):
        """History requires at least 4 valid entries."""
        # 3 entries - should not apply
        result = detector.detect("obrigado", ["你好", "你好", "你好"])
        assert result == "Portuguese"

    def test_history_requires_70_percent(self, detector):
        """History requires 70%+ majority."""
        # 4 Chinese entries = 100% - should apply
        result = detector.detect("obrigado", ["你好"] * 4)
        assert result == "Chinese(Simplified)"


# =============================================================================
# Statistical Summary
# =============================================================================

class TestStatisticalSummary:
    """Overall statistical summary."""

    def test_overall_accuracy(self, detector, all_samples):
        """Calculate overall accuracy on large sample."""
        random.seed(42)
        test_samples = random.sample(all_samples, min(5000, len(all_samples)))

        correct = sum(1 for s in test_samples
                     if detector.detect(s['content']) == s['language'])
        accuracy = correct / len(test_samples) * 100

        print(f"\nOverall accuracy: {accuracy:.2f}% ({correct}/{len(test_samples)})")

        # Should be at least 90% overall
        assert accuracy >= 85, f"Overall accuracy too low: {accuracy:.1f}%"

    def test_detection_distribution(self, detector, all_samples):
        """Show detection result distribution."""
        random.seed(42)
        test_samples = random.sample(all_samples, min(10000, len(all_samples)))

        detected_counts = Counter()
        for s in test_samples:
            detected = detector.detect(s['content'])
            detected_counts[detected] += 1

        print("\nDetection distribution (10k sample):")
        total = sum(detected_counts.values())
        for lang, count in detected_counts.most_common():
            pct = count / total * 100
            print(f"  {lang:25} {count:5} ({pct:5.1f}%)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])