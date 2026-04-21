"""
V4 Evaluation Script — ReviewSense Analytics
Uses the SAME pipeline as the FastAPI /predict endpoint.

Usage:
    python -m scripts.full_evaluation           # Normal mode
    python -m scripts.full_evaluation --debug   # Raw model output only
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import json
import random
import argparse
import time
from collections import Counter

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
)

# ── DATASET ──────────────────────────────────────────────────
# Balanced 18 unique samples × 14 = 252 total

dataset = [
    # English — clear positive
    {"text": "This product is amazing, highly recommend it", "label": "positive"},
    {"text": "Excellent quality, exceeded my expectations", "label": "positive"},
    {"text": "Absolutely loved it, five stars", "label": "positive"},
    # English — clear negative
    {"text": "Worst experience ever, do not buy this", "label": "negative"},
    {"text": "Terrible quality, waste of money", "label": "negative"},
    {"text": "Very bad product, I returned it immediately", "label": "negative"},
    # English — neutral
    {"text": "It is okay, nothing special about this product", "label": "neutral"},
    {"text": "Average quality, meets basic expectations", "label": "neutral"},
    {"text": "Arrived on time, standard packaging", "label": "neutral"},
    # Hindi
    {"text": "\u092f\u0939 \u092c\u0939\u0941\u0924 \u0905\u091a\u094d\u091b\u093e \u0939\u0948, \u092e\u0941\u091d\u0947 \u092c\u0939\u0941\u0924 \u092a\u0938\u0902\u0926 \u0906\u092f\u093e", "label": "positive"},
    {"text": "\u092f\u0939 \u092c\u0939\u0941\u0924 \u0916\u0930\u093e\u092c \u0939\u0948, \u092c\u093f\u0932\u094d\u0915\u0941\u0932 \u092c\u0947\u0915\u093e\u0930", "label": "negative"},
    {"text": "\u0920\u0940\u0915 \u0939\u0948, \u0915\u0941\u091b \u0916\u093e\u0938 \u0928\u0939\u0940\u0902", "label": "neutral"},
    # French
    {"text": "Ce produit est excellent, je le recommande", "label": "positive"},
    {"text": "C'est horrible, tr\u00e8s mauvaise qualit\u00e9", "label": "negative"},
    {"text": "C'est moyen, rien de sp\u00e9cial", "label": "neutral"},
    # German
    {"text": "Das ist fantastisch, sehr gute Qualit\u00e4t", "label": "positive"},
    {"text": "Sehr schlecht, ich bin entt\u00e4uscht", "label": "negative"},
    {"text": "Es ist okay, nichts Besonderes", "label": "neutral"},
]

# Expand to ~250 samples
dataset = dataset * 14
random.seed(42)
random.shuffle(dataset)


# ── PREDICTION ───────────────────────────────────────────────

def predict_direct(text: str, debug: bool = False) -> dict:
    """Use the same pipeline as the API — direct function import."""
    from src.pipeline.inference import run_pipeline
    result = run_pipeline(text)
    label_name = result.get("label_name", "")
    return {
        "label": str(label_name).lower(),
        "confidence": result.get("confidence", 0.0),
        "model_used": result.get("model_used", "unknown"),
        "language_detected": result.get("language_detected", "unknown"),
    }


# ── MAIN ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true",
                        help="Bypass pipeline corrections (raw model output)")
    args = parser.parse_args()

    y_true = []
    y_pred = []
    errors = []

    print(f"\nRunning evaluation on {len(dataset)} samples...\n")
    start = time.perf_counter()

    for item in dataset:
        true_label = item["label"].lower()
        result = predict_direct(item["text"], debug=args.debug)
        pred_label = result["label"].lower()

        y_true.append(true_label)
        y_pred.append(pred_label)

        if pred_label != true_label:
            errors.append({
                "text": item["text"],
                "true": true_label,
                "pred": pred_label,
                "confidence": result.get("confidence", 0),
                "model_used": result.get("model_used", "?"),
            })

    elapsed = time.perf_counter() - start

    # ── METRICS ──────────────────────────────────────────────
    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0,
    )
    cm = confusion_matrix(
        y_true, y_pred, labels=["positive", "negative", "neutral"]
    )
    distribution = Counter(y_pred)

    # ── REPORT ───────────────────────────────────────────────
    mode = "DEBUG (raw model)" if args.debug else "PRODUCTION (full pipeline)"
    print(f"\n{'='*60}")
    print(f"  V4 EVALUATION RESULTS  [{mode}]")
    print(f"{'='*60}")
    print(f"  Samples:   {len(dataset)}")
    print(f"  Time:      {elapsed:.1f}s ({elapsed/len(dataset)*1000:.0f}ms/sample)")
    print(f"  Accuracy:  {accuracy * 100:.1f}%")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1 Score:  {f1:.4f}")

    print(f"\n  Prediction Distribution:")
    for label in ["positive", "negative", "neutral"]:
        count = distribution.get(label, 0)
        pct = count / len(dataset) * 100
        print(f"    {label:>8s}: {count:3d}  ({pct:.1f}%)")

    print(f"\n  Confusion Matrix (Positive, Negative, Neutral):")
    for row in cm:
        print(f"    {row}")

    # ── Neutral rate check ───────────────────────────────────
    neutral_pct = distribution.get("neutral", 0) / len(dataset) * 100
    if neutral_pct > 50:
        print(f"\n  [WARNING] Neutral rate {neutral_pct:.0f}% > 50% — bias detected!")
    else:
        print(f"\n  [OK] Neutral rate {neutral_pct:.0f}% within acceptable range.")

    print(f"  Total Errors: {len(errors)}")

    # Save errors
    try:
        with open("evaluation_errors.json", "w", encoding="utf-8") as f:
            json.dump(errors[:50], f, indent=2, ensure_ascii=False)
        print("  Saved top errors to evaluation_errors.json")
    except Exception:
        pass

    print(f"{'='*60}\n")

    # Return accuracy for programmatic use
    return accuracy


if __name__ == "__main__":
    main()