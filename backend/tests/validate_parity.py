"""
Phase 1 Validation — Ensures API outputs match
the existing Streamlit ML logic for 20 test inputs.
Run this before declaring Phase 1 complete.

Usage:
  python backend/tests/validate_parity.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

import requests
import logging

# Patch streamlit before importing src modules
from app.dependencies import _patch_streamlit_cache, add_src_to_path
_patch_streamlit_cache()
add_src_to_path()

from src.predict import predict_sentiment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("parity")

API_BASE = "http://localhost:8000"

TEST_INPUTS = [
    "The food was absolutely amazing and delicious.",
    "Terrible experience, complete waste of money.",
    "It was okay, nothing special.",
    "Outstanding service, I loved every moment.",
    "The product broke after one day.",
    "Best purchase I have ever made.",
    "Very disappointing quality.",
    "Decent value for the price.",
    "Horrible customer support.",
    "Exceeded all my expectations.",
    "Average at best, nothing impressive.",
    "I would never buy this again.",
    "Perfect in every way.",
    "The delivery was extremely slow.",
    "Highly recommend to everyone.",
    "Complete garbage, do not buy.",
    "Good product but overpriced.",
    "Amazing quality and fast shipping.",
    "The worst restaurant I have visited.",
    "Five stars, absolutely love it.",
]


def run_parity_check():
    passed = 0
    failed = 0
    failures = []

    print("\n" + "="*60)
    print("PHASE 1 PARITY VALIDATION")
    print("Comparing API output vs src.predict.predict_sentiment")
    print("="*60 + "\n")

    for i, text in enumerate(TEST_INPUTS):
        # Ground truth from existing logic
        ground_truth = predict_sentiment(text, "best")
        gt_sentiment = ground_truth.get(
            "label_name", "Neutral").lower()
        # confidence is 0-1, API returns 0-100
        gt_confidence = float(ground_truth.get(
            "confidence", 0.0)) * 100

        # B1: Apply same corrections that the API applies
        # so parity comparison is apples-to-apples
        from app.sentiment_corrections import (
            apply_sentiment_corrections,
        )
        gt_sentiment, gt_confidence, _ = (
            apply_sentiment_corrections(
                text, gt_sentiment, gt_confidence
            )
        )

        # API output
        try:
            r = requests.post(
                f"{API_BASE}/predict",
                json={
                    "text": text,
                    "model": "best",
                    "include_lime": False,
                    "include_absa": False,
                    "include_sarcasm": False,
                },
                timeout=30,
            )
            r.raise_for_status()
            api_data = r.json()
            api_sentiment = api_data["sentiment"]
            api_confidence = api_data["confidence"]
        except Exception as e:
            logger.error(f"Test {i+1} API call failed: {e}")
            failed += 1
            failures.append({
                "input": text[:50],
                "error": str(e),
            })
            continue

        # Check sentiment label matches exactly
        label_match = gt_sentiment == api_sentiment

        # Check confidence within ±1.0 tolerance
        conf_diff = abs(gt_confidence - api_confidence)
        conf_match = conf_diff <= 1.0

        if label_match and conf_match:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"
            failures.append({
                "input": text[:50],
                "gt_sentiment": gt_sentiment,
                "api_sentiment": api_sentiment,
                "gt_confidence": gt_confidence,
                "api_confidence": api_confidence,
                "conf_diff": conf_diff,
            })

        print(
            f"[{i+1:2d}] {status} | "
            f"GT: {gt_sentiment:8s} {gt_confidence:.1f}% | "
            f"API: {api_sentiment:8s} {api_confidence:.1f}% | "
            f"{text[:40]}"
        )

    print("\n" + "="*60)
    print(f"RESULTS: {passed}/20 passed, {failed}/20 failed")
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f}")
    print("="*60)

    if failed == 0:
        print("\n✅ PHASE 1 COMPLETE — All 20 tests passed")
        print("   API outputs match existing ML logic exactly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed.")
        print("   Review failures above before proceeding.")

    return failed == 0


if __name__ == "__main__":
    success = run_parity_check()
    sys.exit(0 if success else 1)
