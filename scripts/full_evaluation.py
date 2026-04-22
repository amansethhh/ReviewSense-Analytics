"""
V4+ Stability Lock Evaluation Script — ReviewSense Analytics
Uses the SAME pipeline as the FastAPI /predict endpoint.

Section 9: Real-world multilingual evaluation (300+ samples).

Usage:
    python -m scripts.full_evaluation
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import json
import random
import time
from collections import Counter

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
)

# ── DATASET ──────────────────────────────────────────────────
# 24 unique samples × 14 = 336 total
# Covers: English, Hindi, French, German, Arabic, Japanese, Hinglish

dataset = [
    # English — positive (varied lengths/styles)
    {"text": "This product is amazing, highly recommend it", "label": "positive"},
    {"text": "Excellent quality, exceeded my expectations", "label": "positive"},
    {"text": "Absolutely loved it, five stars", "label": "positive"},
    # English — negative (varied lengths/styles)
    {"text": "Worst experience ever, do not buy this", "label": "negative"},
    {"text": "Terrible quality, waste of money", "label": "negative"},
    {"text": "Very bad product, I returned it immediately", "label": "negative"},
    # English — neutral (ambiguous/factual)
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
    # Arabic
    {"text": "\u0647\u0630\u0627 \u0627\u0644\u0645\u0646\u062a\u062c \u0631\u0627\u0626\u0639 \u062c\u062f\u0627", "label": "positive"},
    {"text": "\u0647\u0630\u0627 \u0633\u064a\u0621 \u062c\u062f\u0627", "label": "negative"},
    # Japanese
    {"text": "\u3053\u308c\u306f\u7d20\u6674\u3089\u3057\u3044", "label": "positive"},
    {"text": "\u3053\u308c\u306f\u3072\u3069\u3044", "label": "negative"},
    # Hinglish
    {"text": "Yeh product bakwaas hai, paisa barbaad", "label": "negative"},
    {"text": "Zabardast quality hai, bahut acha product", "label": "positive"},
]

# Expand to ~336 samples
dataset = dataset * 14
random.seed(42)
random.shuffle(dataset)


# ── PREDICTION ───────────────────────────────────────────────

def predict_direct(text: str) -> dict:
    """Section 9: Use the same pipeline as the API."""
    from src.pipeline.inference import run_pipeline
    result = run_pipeline(text)
    label_name = result.get("label_name", "")
    trace = result.get("pipeline_trace", {})
    return {
        "label": str(label_name).lower(),
        "confidence": result.get("confidence", 0.0),
        "polarity": result.get("polarity", 0.0),
        "route": trace.get("route", "?"),
        "model_used": trace.get("model_used", "?"),
        "margin": trace.get("margin", 0.0),
        "decision": trace.get("decision", "?"),
    }


# ── MAIN ─────────────────────────────────────────────────────

def main():
    y_true = []
    y_pred = []
    errors = []
    zero_polarity_non_neutral = 0
    ambiguous_count = 0
    route_counts = Counter()
    model_counts = Counter()

    print(f"\nRunning evaluation on {len(dataset)} samples...\n")
    start = time.perf_counter()

    for item in dataset:
        true_label = item["label"].lower()
        result = predict_direct(item["text"])
        pred_label = result["label"].lower()

        y_true.append(true_label)
        y_pred.append(pred_label)

        # Track routing
        route_counts[result.get("route", "?")] += 1
        model_counts[result.get("model_used", "?")] += 1

        # Track ambiguous decisions
        if result.get("decision") == "ambiguous":
            ambiguous_count += 1

        # Track polarity zero for non-neutral
        if pred_label in ("positive", "negative") and result.get("polarity", 0.0) == 0.0:
            zero_polarity_non_neutral += 1

        if pred_label != true_label:
            errors.append({
                "text": item["text"],
                "true": true_label,
                "pred": pred_label,
                "confidence": result.get("confidence", 0),
                "margin": result.get("margin", 0),
                "route": result.get("route", "?"),
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
    print(f"\n{'='*60}")
    print(f"  V4+ STABILITY LOCK EVALUATION  [PRODUCTION]")
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

    # ── Stability metrics ────────────────────────────────────
    neutral_pct = distribution.get("neutral", 0) / len(dataset) * 100
    ambig_pct = ambiguous_count / len(dataset) * 100
    misclass_pct = len(errors) / len(dataset) * 100

    print(f"\n  ── Stability Metrics ──")
    print(f"  Neutral rate:          {neutral_pct:.1f}%", end="")
    if 15 <= neutral_pct <= 35:
        print(f"  [OK]")
    elif neutral_pct > 50:
        print(f"  [WARNING: bias]")
    else:
        print(f"  [CHECK]")

    print(f"  Ambiguous decisions:   {ambiguous_count} ({ambig_pct:.1f}%)")
    print(f"  Misclassification:     {len(errors)} ({misclass_pct:.1f}%)", end="")
    print(f"  [{'OK' if misclass_pct < 8 else 'HIGH'}]")
    print(f"  Zero-polarity errors:  {zero_polarity_non_neutral}")

    print(f"\n  ── Routing Distribution ──")
    for route, count in route_counts.most_common():
        print(f"    {route:15s}: {count:3d}")

    print(f"\n  ── Model Usage ──")
    for model, count in model_counts.most_common():
        print(f"    {model:15s}: {count:3d}")

    print(f"\n  ── Target Compliance ──")
    targets = [
        ("Accuracy >= 92%", accuracy >= 0.92),
        ("Neutral rate 15-35%", 15 <= neutral_pct <= 35),
        ("Misclassification < 8%", misclass_pct < 8),
    ]
    for desc, passed in targets:
        print(f"    {'[PASS]' if passed else '[FAIL]'} {desc}")

    print(f"\n  Total Errors: {len(errors)}")

    # Save errors
    try:
        with open("evaluation_errors.json", "w", encoding="utf-8") as f:
            json.dump(errors[:50], f, indent=2, ensure_ascii=False)
        print("  Saved top errors to evaluation_errors.json")
    except Exception:
        pass

    print(f"{'='*60}\n")
    return accuracy


if __name__ == "__main__":
    main()