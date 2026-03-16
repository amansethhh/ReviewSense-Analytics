"""
scripts/verify_model.py
-----------------------
Verification script for ReviewSense Analytics sentiment pipeline.

Loads the best model and runs predictions on known-sentiment test sentences.
Reports predictions, confidence scores, and pass/fail status.

Usage:
    python scripts/verify_model.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.predict import load_model, predict_sentiment
from src.preprocess import preprocess_pipeline


def main():
    print("=" * 70)
    print("  ReviewSense Analytics — Model Verification")
    print("=" * 70)

    # ── Load best model ───────────────────────────────────────────────────
    print("\nLoading best model...")
    try:
        model_pipeline, label_map = load_model("best")
        print(f"  ✓ Model loaded successfully")
        print(f"  ✓ Label map: {label_map}")
    except Exception as e:
        print(f"  ✗ Failed to load model: {e}")
        sys.exit(1)

    # ── Test sentences ────────────────────────────────────────────────────
    test_cases = [
        # (text, expected_label, expected_label_name)
        # Negative
        ("The food is so bad", 0, "Negative"),
        ("This product is terrible", 0, "Negative"),
        ("I hate this service", 0, "Negative"),
        ("The worst experience ever", 0, "Negative"),
        ("Very disappointed with the quality", 0, "Negative"),
        ("Awful product, complete waste of money", 0, "Negative"),
        # Positive
        ("This product is amazing", 2, "Positive"),
        ("I love this phone", 2, "Positive"),
        ("The service was excellent", 2, "Positive"),
        ("Best purchase I have ever made", 2, "Positive"),
        ("Outstanding quality and great value", 2, "Positive"),
        # Neutral
        ("The food was okay", 1, "Neutral"),
        ("The product is average", 1, "Neutral"),
        ("It works as expected, nothing special", 1, "Neutral"),
    ]

    print("\n" + "-" * 70)
    print(f"  {'Input':<42s} {'Expected':<10s} {'Predicted':<10s} {'Conf':>6s} {'Status'}")
    print("-" * 70)

    passed = 0
    failed = 0
    results = []

    for text, expected_label, expected_name in test_cases:
        result = predict_sentiment(text, model_pipeline)
        pred_label = result["label"]
        pred_name = result["label_name"]
        confidence = result["confidence"]
        polarity = result["polarity"]

        is_correct = pred_label == expected_label
        status = "✅ PASS" if is_correct else "❌ FAIL"

        if is_correct:
            passed += 1
        else:
            failed += 1

        # Show preprocessed form for debugging
        preprocessed = preprocess_pipeline(text) or text.strip().lower()

        print(f"  \"{text:<40s}\" {expected_name:<10s} {pred_name:<10s} {confidence*100:>5.1f}% {status}")

        results.append({
            "text": text,
            "preprocessed": preprocessed,
            "expected": expected_name,
            "predicted": pred_name,
            "confidence": confidence,
            "polarity": polarity,
            "correct": is_correct,
        })

    # ── Summary ───────────────────────────────────────────────────────────
    total = passed + failed
    print("\n" + "=" * 70)
    print(f"  Results: {passed}/{total} passed ({passed/total*100:.0f}%)")

    if failed > 0:
        print(f"\n  ❌ {failed} test(s) FAILED:")
        for r in results:
            if not r["correct"]:
                print(f"     \"{r['text']}\"")
                print(f"       preprocessed: \"{r['preprocessed']}\"")
                print(f"       expected: {r['expected']}, got: {r['predicted']} (conf: {r['confidence']*100:.1f}%)")
                print(f"       polarity: {r['polarity']:.3f}")
    else:
        print("  ✅ All tests PASSED!")

    print("=" * 70)

    # Return exit code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
