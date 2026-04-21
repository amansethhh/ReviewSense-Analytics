"""
V3 Verification Tests — ReviewSense Analytics Restoration

Tests the critical fixes from the V3 Definitive Restoration:
1. Three-class output contract (no UNCERTAIN labels)
2. Polarity computation with translated_text parameter
3. Translation degenerate detection (template patterns)
4. Sarcasm superlative exclusion guard
5. Validator safety middleware
6. Language detection kana priority (Japanese ≠ Chinese)
"""

import sys
import os
import re

# Ensure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


# ═══════════════════════════════════════════════════════════════
# TEST 1: Three-class output contract — UNCERTAIN NEVER appears
# ═══════════════════════════════════════════════════════════════

def test_enforce_uncertainty_never_returns_uncertain():
    """V3 MANDATE: enforce_uncertainty() must NEVER return 'uncertain'."""
    from app.utils.output_contract import enforce_uncertainty

    # Low confidence — was previously "uncertain"
    label, raw, is_uncertain = enforce_uncertainty("neutral", 40.0)
    assert label == "neutral", f"Expected 'neutral', got '{label}'"
    assert is_uncertain is True
    assert raw == "neutral"

    # Low confidence positive — was previously "uncertain"
    label, raw, is_uncertain = enforce_uncertainty("positive", 30.0)
    assert label == "positive", f"Expected 'positive', got '{label}'"
    assert is_uncertain is True

    # High confidence — always passed through
    label, raw, is_uncertain = enforce_uncertainty("negative", 85.0)
    assert label == "negative", f"Expected 'negative', got '{label}'"
    assert is_uncertain is False

    # Edge case — exactly at threshold
    label, raw, is_uncertain = enforce_uncertainty("positive", 65.0)
    assert label == "positive", f"Expected 'positive', got '{label}'"
    assert is_uncertain is False

    # CRITICAL: No label should EVER be "uncertain"
    for sentiment in ["positive", "negative", "neutral"]:
        for conf in [0.0, 10.0, 30.0, 50.0, 64.9, 65.0, 80.0, 100.0]:
            label, _, _ = enforce_uncertainty(sentiment, conf)
            assert label != "uncertain", (
                f"VIOLATION: enforce_uncertainty({sentiment}, {conf}) "
                f"returned 'uncertain'"
            )

    print("  ✅ TEST 1 PASSED: UNCERTAIN label completely eliminated")


# ═══════════════════════════════════════════════════════════════
# TEST 2: compute_dual_polarity accepts translated_text
# ═══════════════════════════════════════════════════════════════

def test_compute_dual_polarity_translated_text():
    """V3 FIX: Non-Latin reviews should use translated_text for polarity."""
    from src.predict import compute_dual_polarity

    # English text — should compute directly
    tb, vader, subj = compute_dual_polarity(
        "This product is absolutely fantastic and I love it!",
        "en",
    )
    assert tb != 0.0 or subj != 0.5, (
        f"English text should NOT return default (0,0,0.5), got "
        f"({tb}, {vader}, {subj})"
    )

    # Japanese text WITHOUT translation — should return defaults
    tb, vader, subj = compute_dual_polarity(
        "この製品は素晴らしいです",
        "ja",
        translated_text=None,
    )
    assert tb == 0.0 and subj == 0.5, (
        f"Japanese without translation should return (0,0,0.5), got "
        f"({tb}, {vader}, {subj})"
    )

    # Japanese text WITH translation — should compute from translation
    tb, vader, subj = compute_dual_polarity(
        "この製品は素晴らしいです",
        "ja",
        translated_text="This product is wonderful and amazing",
    )
    assert tb != 0.0 or subj != 0.5, (
        f"Japanese WITH translation should NOT return (0,0,0.5), got "
        f"({tb}, {vader}, {subj})"
    )

    print("  ✅ TEST 2 PASSED: compute_dual_polarity uses translated_text")


# ═══════════════════════════════════════════════════════════════
# TEST 3: Degenerate translation detection (template patterns)
# ═══════════════════════════════════════════════════════════════

def test_degenerate_translation_detection():
    """V3 FIX: Template translations must be detected as degenerate."""
    from src.models.translation import _is_degenerate

    # Known degenerate patterns
    assert _is_degenerate("原始テキスト", "The product is great.") is True
    assert _is_degenerate("原始テキスト", "The quality is decent.") is True
    assert _is_degenerate("原始テキスト", "Bad experience.") is True
    assert _is_degenerate("原始テキスト", "This product is good.") is True

    # V3: Template fallback patterns
    assert _is_degenerate("原始テキスト", "The product is excellent.") is True
    assert _is_degenerate("原始テキスト", "Very disappointing.") is True
    assert _is_degenerate("原始テキスト", "Works perfectly.") is True

    # Leaked language tags
    assert _is_degenerate("text", "Good product [Chinese]") is True
    assert _is_degenerate("text", "[Japanese]") is True

    # Valid translations should NOT be flagged
    assert _is_degenerate(
        "この製品は素晴らしいです",
        "This product is wonderful and I really enjoy using it every day"
    ) is False

    print("  ✅ TEST 3 PASSED: Degenerate translation patterns detected")


# ═══════════════════════════════════════════════════════════════
# TEST 4: Sarcasm superlative exclusion guard
# ═══════════════════════════════════════════════════════════════

def test_sarcasm_superlative_exclusion():
    """V3 FIX: 'incredibly fast' in positive reviews must NOT be sarcasm."""
    from src.sarcasm_detector import _sarcasm_exclusion_check

    # Superlative in high-confidence positive → NOT sarcasm
    result = _sarcasm_exclusion_check(
        "This phone is incredibly fast and I absolutely love it",
        confidence=0.85,
        pred_class=2,
    )
    assert result is not None, "Superlative positive should be excluded"
    assert result["is_sarcastic"] is False
    assert result["reason"] == "superlative_positive_excluded"

    # Superlative with negative words → proceed with detection
    result = _sarcasm_exclusion_check(
        "This phone is incredibly fast but terrible battery life",
        confidence=0.85,
        pred_class=2,
    )
    assert result is None, "Superlative with negatives should NOT be excluded"

    # Low confidence → excluded by low_confidence check
    result = _sarcasm_exclusion_check(
        "This is incredibly bad and I hate it so much",
        confidence=0.40,
        pred_class=0,
    )
    assert result is not None
    assert result["reason"] == "low_confidence_excluded"

    print("  ✅ TEST 4 PASSED: Superlative exclusion guard works")


# ═══════════════════════════════════════════════════════════════
# TEST 5: Validator safety middleware
# ═══════════════════════════════════════════════════════════════

def test_validator_middleware():
    """V3 FIX: Validator must catch and correct forbidden labels."""
    from app.utils.validator import validate_prediction_output, VALID_LABELS

    # "uncertain" must be corrected to "neutral"
    result = validate_prediction_output({
        "sentiment": "uncertain",
        "confidence": 45.0,
        "polarity": 0.1,
        "subjectivity": 0.5,
    })
    assert result["sentiment"] == "neutral", (
        f"Expected 'neutral', got '{result['sentiment']}'"
    )

    # "unknown" must be corrected to "neutral"
    result = validate_prediction_output({
        "sentiment": "unknown",
        "confidence": 0.0,
    })
    assert result["sentiment"] == "neutral"

    # Valid labels must pass through unchanged
    for label in VALID_LABELS:
        result = validate_prediction_output({
            "sentiment": label,
            "confidence": 75.0,
            "polarity": 0.3,
            "subjectivity": 0.6,
        })
        assert result["sentiment"] == label

    # Confidence bounds
    result = validate_prediction_output({
        "sentiment": "positive",
        "confidence": 150.0,
    })
    assert result["confidence"] == 100.0

    result = validate_prediction_output({
        "sentiment": "negative",
        "confidence": -10.0,
    })
    assert result["confidence"] == 0.0

    print("  ✅ TEST 5 PASSED: Validator middleware catches violations")


# ═══════════════════════════════════════════════════════════════
# TEST 6: Language detection — Japanese ≠ Chinese
# ═══════════════════════════════════════════════════════════════

def test_japanese_chinese_detection():
    """V3 VERIFY: Japanese text must NOT be classified as Chinese."""
    from app.utils.language_detection import detect_script_unicode

    # Pure Japanese (Hiragana + Katakana + Kanji)
    assert detect_script_unicode("この製品は素晴らしいです") == "ja"
    assert detect_script_unicode("カメラの品質がとても良い") == "ja"

    # Pure Chinese (CJK only, no kana)
    assert detect_script_unicode("这个产品非常好") == "zh-cn"
    assert detect_script_unicode("质量很差不推荐购买") == "zh-cn"

    # Korean
    assert detect_script_unicode("이 제품은 정말 좋습니다") == "ko"

    # Arabic
    assert detect_script_unicode("هذا المنتج ممتاز جدا") == "ar"

    print("  ✅ TEST 6 PASSED: Japanese ≠ Chinese detection correct")


# ═══════════════════════════════════════════════════════════════
# TEST 7: translate_to_english returns tuple
# ═══════════════════════════════════════════════════════════════

def test_translate_to_english_returns_tuple():
    """V3 CONTRACT: translate_to_english must return (text, method) tuple."""
    from src.models.translation import translate_to_english

    # English passthrough
    result = translate_to_english("Hello world", src_lang="en")
    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2
    text, method = result
    assert text == "Hello world"
    assert method == "passthrough"

    # Empty text
    result = translate_to_english("", src_lang="ja")
    assert isinstance(result, tuple)
    text, method = result
    assert method == "passthrough"

    print("  ✅ TEST 7 PASSED: translate_to_english returns tuple")


# ═══════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  V3 VERIFICATION TESTS — ReviewSense Analytics")
    print("=" * 60 + "\n")

    tests = [
        ("1. Three-class output contract", test_enforce_uncertainty_never_returns_uncertain),
        ("2. Polarity with translated_text", test_compute_dual_polarity_translated_text),
        ("3. Degenerate translation detection", test_degenerate_translation_detection),
        ("4. Sarcasm superlative exclusion", test_sarcasm_superlative_exclusion),
        ("5. Validator safety middleware", test_validator_middleware),
        ("6. Japanese ≠ Chinese detection", test_japanese_chinese_detection),
        ("7. translate_to_english tuple contract", test_translate_to_english_returns_tuple),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: FAILED — {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {passed}/{passed + failed} passed")
    if failed == 0:
        print("  🎉 ALL V3 VERIFICATION TESTS PASSED")
    else:
        print(f"  ⚠️  {failed} test(s) FAILED — review output above")
    print(f"{'=' * 60}\n")
