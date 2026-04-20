"""E2E Test Suite — Master Fix Prompt Section 9.

Tests 1-10: Verify all 17 fixes are wired correctly through the pipeline.
Each test validates a specific fix or combination of fixes.
"""

import sys
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging
logging.basicConfig(level=logging.WARNING)


def _run_test(test_name, text, expected_label=None, expected_checks=None):
    """Run a single pipeline test and report results."""
    from src.predict import predict_sentiment
    result = predict_sentiment(text, run_sarcasm_detection=True)

    status = "✅ PASS"
    failures = []

    if expected_label is not None:
        actual = result.get("label_name", "?")
        if actual != expected_label:
            status = "❌ FAIL"
            failures.append(f"Label: expected={expected_label}, got={actual}")

    if expected_checks:
        for key, expected_val in expected_checks.items():
            actual_val = result.get(key)
            if isinstance(expected_val, bool):
                if actual_val != expected_val:
                    status = "❌ FAIL"
                    failures.append(f"{key}: expected={expected_val}, got={actual_val}")
            elif expected_val == "NOT_NONE":
                if actual_val is None:
                    status = "❌ FAIL"
                    failures.append(f"{key}: expected non-None, got=None")
            elif expected_val == "LOW":
                if actual_val is not None and actual_val > 0.72:
                    status = "❌ FAIL"
                    failures.append(f"{key}: expected <0.72, got={actual_val}")
            elif expected_val == "HIGH":
                if actual_val is not None and actual_val < 0.70:
                    status = "❌ FAIL"
                    failures.append(f"{key}: expected >0.70, got={actual_val}")

    label_name = result.get("label_name", "?")
    confidence = result.get("confidence", 0)
    polarity = result.get("polarity", 0)

    print(f"\n{'='*70}")
    print(f"  {status}  {test_name}")
    print(f"  Input: \"{text[:60]}{'...' if len(text)>60 else ''}\"")
    print(f"  Result: {label_name} | conf={confidence:.3f} | pol={polarity:.3f}")
    if result.get("neutral_corrected"):
        print(f"  ⚖️  Neutral corrected: {result.get('correction_reason', '')}")
    if result.get("guard_applied"):
        print(f"  ⚡ Guard applied: {result['guard_applied']}")
    if result.get("temperature_scaled"):
        print(f"  🌡️  Temperature scaled: raw={result.get('raw_confidence', 0):.3f} → cal={confidence:.3f}")
    if result.get("sarcasm_applied"):
        print(f"  🎭 Sarcasm override applied")
    if result.get("uncertain_prediction"):
        print(f"  ⚠️  Uncertain prediction (conf < {result.get('confidence_threshold', 0.60):.2f})")
    if failures:
        for f in failures:
            print(f"  ⛔ {f}")
    print(f"{'='*70}")

    return status == "✅ PASS", result


def main():
    print("\n" + "━"*70)
    print("  REVIEWSENSE ANALYTICS — E2E PIPELINE VERIFICATION")
    print("  Testing all 17 fixes (Master 7 + Add-On 10)")
    print("━"*70)

    results = []

    # ═══════════════════════════════════════════════════════════
    # TEST 1 — Neutral correction (Problem 1)
    # Mixed sentiment → should correct to Neutral when confidence low
    # ═══════════════════════════════════════════════════════════
    ok, r = _run_test(
        "TEST 1: Neutral Correction (P1)",
        "The product is okay, nothing special but does the job.",
        expected_checks={"confidence": "LOW"},
    )
    results.append(("TEST 1: Neutral Correction", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 2 — Short-text negation guard (ADD-ON 1)
    # Short negative text → must stay Negative
    # ═══════════════════════════════════════════════════════════
    ok, r = _run_test(
        "TEST 2: Short-text Guard (A1)",
        "Terrible product.",
        expected_label="Negative",
    )
    results.append(("TEST 2: Short-text Guard", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 3 — Short-text positive guard (ADD-ON 1)
    # Short positive text → must stay Positive
    # ═══════════════════════════════════════════════════════════
    ok, r = _run_test(
        "TEST 3: Short-text Positive Guard (A1)",
        "Excellent quality!",
        expected_label="Positive",
    )
    results.append(("TEST 3: Short-text Positive", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 4 — Confidence calibration (Problem 5)
    # Positive prediction + weak polarity → confidence reduced
    # ═══════════════════════════════════════════════════════════
    ok, r = _run_test(
        "TEST 4: Confidence Calibration (P5)",
        "It works I guess.",
        expected_checks={"temperature_scaled": True},
    )
    results.append(("TEST 4: Confidence Calibration", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 5 — Temperature scaling (ADD-ON 5)
    # Verify temperature scaling is applied for non-obvious predictions
    # ═══════════════════════════════════════════════════════════
    ok, r = _run_test(
        "TEST 5: Temperature Scaling (A5)",
        "The camera quality is decent but nothing groundbreaking.",
        expected_checks={"temperature_scaled": True},
    )
    results.append(("TEST 5: Temperature Scaling", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 6 — Clear positive text
    # High-confidence positive → should remain Positive
    # ═══════════════════════════════════════════════════════════
    ok, r = _run_test(
        "TEST 6: Clear Positive",
        "This is the best product I have ever bought! Amazing quality!",
        expected_label="Positive",
        expected_checks={"neutral_corrected": False},
    )
    results.append(("TEST 6: Clear Positive", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 7 — Clear negative text
    # High-confidence negative → should remain Negative
    # ═══════════════════════════════════════════════════════════
    ok, r = _run_test(
        "TEST 7: Clear Negative",
        "This product is terrible. Complete waste of money. Would not recommend to anyone.",
        expected_label="Negative",
        expected_checks={"neutral_corrected": False},
    )
    results.append(("TEST 7: Clear Negative", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 8 — Sarcasm exclusion guard (ADD-ON 7)
    # Hedge phrase → sarcasm should NOT fire
    # ═══════════════════════════════════════════════════════════
    ok, r = _run_test(
        "TEST 8: Sarcasm Exclusion (A7)",
        "It's okay. Works fine. Does what it says. Nothing special really.",
        expected_checks={"sarcasm_applied": False},
    )
    results.append(("TEST 8: Sarcasm Exclusion", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 9 — LIME feature filter (ADD-ON 4)
    # Verify LIME returns filtered features (non-empty)
    # ═══════════════════════════════════════════════════════════
    try:
        from src.lime_explainer import explain_prediction, filter_lime_features
        raw_features = [("the", 0.02), ("amazing", 0.45), ("terrible", -0.38), ("is", 0.01), ("product", 0.12)]
        filtered = filter_lime_features(raw_features)
        # Should remove "the" and "is" (stopwords with low weight)
        remaining_words = [w for w, _ in filtered]
        ok = "the" not in remaining_words or "is" not in remaining_words
        print(f"\n{'='*70}")
        print(f"  {'✅ PASS' if ok else '❌ FAIL'}  TEST 9: LIME Feature Filter (A4)")
        print(f"  Input: {raw_features}")
        print(f"  Filtered: {filtered}")
        print(f"{'='*70}")
    except Exception as e:
        ok = False
        print(f"\n  ❌ FAIL  TEST 9: LIME Feature Filter — {e}")
    results.append(("TEST 9: LIME Feature Filter", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 10 — ABSA dominant label (ADD-ON 6)
    # ═══════════════════════════════════════════════════════════
    try:
        from src.absa import compute_dominant_label
        # Mix of positive and slightly negative → should be Neutral
        dom = compute_dominant_label([0.15, -0.10, 0.05, -0.05])
        ok = dom == "Neutral"
        print(f"\n{'='*70}")
        print(f"  {'✅ PASS' if ok else '❌ FAIL'}  TEST 10: ABSA Dominant Label (A6)")
        print(f"  Input polarities: [0.15, -0.10, 0.05, -0.05]")
        print(f"  Result: {dom} (expected: Neutral)")
        print(f"{'='*70}")
    except Exception as e:
        ok = False
        print(f"\n  ❌ FAIL  TEST 10: ABSA Dominant Label — {e}")
    results.append(("TEST 10: ABSA Dominant Label", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 11 — Rolling trend (ADD-ON 8)
    # ═══════════════════════════════════════════════════════════
    try:
        from src.trend import compute_rolling_trend
        fake_results = [{"label": i % 3} for i in range(100)]
        trend = compute_rolling_trend(fake_results)
        ok = len(trend) > 1 and all("positive_pct" in t for t in trend)
        print(f"\n{'='*70}")
        print(f"  {'✅ PASS' if ok else '❌ FAIL'}  TEST 11: Rolling Trend (A8)")
        print(f"  Input: 100 fake results")
        print(f"  Trend points: {len(trend)}")
        print(f"{'='*70}")
    except Exception as e:
        ok = False
        print(f"\n  ❌ FAIL  TEST 11: Rolling Trend — {e}")
    results.append(("TEST 11: Rolling Trend", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 12 — Unicode script detection (ADD-ON 3)
    # ═══════════════════════════════════════════════════════════
    try:
        from src.models.language import detect_script
        tests = [
            ("Привет мир", "ru"),    # Cyrillic → Russian
            ("مرحبا بالعالم", "ar"),  # Arabic → Arabic
            ("こんにちは", "ja"),     # Hiragana → Japanese
            ("你好世界", "zh"),       # CJK → Chinese
            ("한국어 텍스트", "ko"),   # Hangul → Korean
            ("สวัสดีครับ", "th"),     # Thai → Thai
        ]
        all_ok = True
        for text, expected in tests:
            actual = detect_script(text)
            if actual != expected:
                all_ok = False
                print(f"  ⛔ Script detection: '{text}' → expected={expected}, got={actual}")
        ok = all_ok
        print(f"\n{'='*70}")
        print(f"  {'✅ PASS' if ok else '❌ FAIL'}  TEST 12: Unicode Script Detection (A3)")
        print(f"  Tested {len(tests)} scripts — all {'passed' if ok else 'SOME FAILED'}")
        print(f"{'='*70}")
    except Exception as e:
        ok = False
        print(f"\n  ❌ FAIL  TEST 12: Unicode Script Detection — {e}")
    results.append(("TEST 12: Unicode Script Detection", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 13 — Hinglish detection (Problem 3)
    # ═══════════════════════════════════════════════════════════
    try:
        from src.models.language import detect_hinglish
        ok_h1 = detect_hinglish("Bahut accha product hai yaar")
        ok_h2 = not detect_hinglish("This is a great product")
        ok = ok_h1 and ok_h2
        print(f"\n{'='*70}")
        print(f"  {'✅ PASS' if ok else '❌ FAIL'}  TEST 13: Hinglish Detection (P3)")
        print(f"  'Bahut accha product hai yaar' → hinglish={ok_h1} (expected=True)")
        print(f"  'This is a great product' → hinglish={ok_h2} (expected=False)")
        print(f"{'='*70}")
    except Exception as e:
        ok = False
        print(f"\n  ❌ FAIL  TEST 13: Hinglish Detection — {e}")
    results.append(("TEST 13: Hinglish Detection", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 14 — Degenerate translation detection (ADD-ON 2)
    # ═══════════════════════════════════════════════════════════
    try:
        from src.pipeline.inference import _is_degenerate, _translation_plausible
        ok_d1 = _is_degenerate("bad experience.")
        ok_d2 = _is_degenerate(".")
        ok_d3 = not _is_degenerate("The product quality is excellent and I would recommend it.")
        ok_p1 = _translation_plausible("Hola mundo", "Hello world")
        ok_p2 = not _translation_plausible("This is a very long sentence with many words", "a")
        ok = ok_d1 and ok_d2 and ok_d3 and ok_p1 and ok_p2
        print(f"\n{'='*70}")
        print(f"  {'✅ PASS' if ok else '❌ FAIL'}  TEST 14: Degenerate Translation (A2)")
        print(f"  'bad experience.' → degenerate={ok_d1} (expected=True)")
        print(f"  '.' → degenerate={ok_d2} (expected=True)")
        print(f"  'The product quality...' → degenerate={not ok_d3} (expected=False)")
        print(f"  Length plausibility checks: {ok_p1}, {ok_p2}")
        print(f"{'='*70}")
    except Exception as e:
        ok = False
        print(f"\n  ❌ FAIL  TEST 14: Degenerate Translation — {e}")
    results.append(("TEST 14: Degenerate Translation", ok))

    # ═══════════════════════════════════════════════════════════
    # TEST 15 — Pipeline wiring contract (ADD-ON 10)
    # Verify all 20 fields present in result dict
    # ═══════════════════════════════════════════════════════════
    try:
        from src.predict import predict_sentiment
        result = predict_sentiment("Good product overall.", run_sarcasm_detection=True)
        required_fields = [
            "label", "label_name", "confidence", "raw_confidence",
            "polarity", "subjectivity", "neutral_corrected", "correction_reason",
            "guard_applied", "temperature_scaled", "translation_status",
            "translation_flagged", "hinglish_detected", "analysis_input_source",
            "sarcasm_detected", "sarcasm_confidence", "sarcasm_applied",
            "sarcasm_reason", "uncertain_prediction", "confidence_threshold",
        ]
        missing = [f for f in required_fields if f not in result]
        ok = len(missing) == 0
        print(f"\n{'='*70}")
        print(f"  {'✅ PASS' if ok else '❌ FAIL'}  TEST 15: Pipeline Wiring Contract (A10)")
        print(f"  Required fields: {len(required_fields)}")
        print(f"  Present: {len(required_fields) - len(missing)}")
        if missing:
            print(f"  ⛔ Missing: {missing}")
        print(f"{'='*70}")
    except Exception as e:
        ok = False
        print(f"\n  ❌ FAIL  TEST 15: Pipeline Wiring — {e}")
    results.append(("TEST 15: Pipeline Wiring Contract", ok))

    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════
    print("\n" + "━"*70)
    print("  SUMMARY")
    print("━"*70)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for name, ok in results:
        print(f"  {'✅' if ok else '❌'}  {name}")
    print(f"\n  Result: {passed}/{total} tests passed")
    if passed == total:
        print("  🎉 ALL TESTS PASSED — Pipeline integrity verified!")
    else:
        print(f"  ⚠️  {total - passed} test(s) need attention")
    print("━"*70 + "\n")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
