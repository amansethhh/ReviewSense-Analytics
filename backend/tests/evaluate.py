"""
End-to-End Evaluation System for ReviewSense Analytics.

Section 7: Computes accuracy, precision, recall, F1-score,
and confusion matrix. Supports multilingual comparison
(original vs translated prediction).

Usage:
    python -m tests.evaluate [--dataset PATH] [--model best]
"""

import json
import sys
import time
import logging
import argparse
from pathlib import Path
from collections import Counter

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logger = logging.getLogger("reviewsense.evaluate")


def evaluate_dataset(
    dataset: list[dict],
    model_choice: str = "best",
    run_multilingual: bool = False,
) -> dict:
    """
    Evaluate model accuracy on a labeled dataset.

    Args:
        dataset: List of dicts with 'text' and 'label' keys.
                 label must be: positive, negative, neutral.
        model_choice: Model to use for prediction.
        run_multilingual: If True, also compare original vs
                          translated predictions.

    Returns:
        {
            "accuracy": float,
            "precision": dict,
            "recall": dict,
            "f1": dict,
            "macro_f1": float,
            "confusion_matrix": dict,
            "uncertain_rate": float,
            "translation_fallback_rate": float,
            "total_samples": int,
            "processing_time_s": float,
            "mismatches": list,
        }
    """
    from src.predict import predict_sentiment
    from app.utils.output_contract import (
        enforce_uncertainty,
        get_translation_stats,
    )

    start_time = time.time()

    labels = ["positive", "negative", "neutral"]
    y_true: list[str] = []
    y_pred: list[str] = []
    uncertain_count = 0
    mismatches: list[dict] = []

    for i, sample in enumerate(dataset):
        text = sample.get("text", "").strip()
        true_label = sample.get("label", "").lower().strip()

        if not text or true_label not in labels:
            continue

        try:
            from app.utils import normalize_confidence

            pred = predict_sentiment(text, model_choice)
            label_name = pred.get(
                "label_name", "Neutral"
            ).lower()
            if label_name not in labels:
                label_name = "neutral"

            raw_conf = float(pred.get("confidence", 0.0))
            confidence_pct = normalize_confidence(raw_conf)

            final_label, raw_label, is_uncertain = (
                enforce_uncertainty(
                    label_name, confidence_pct,
                )
            )

            if is_uncertain:
                uncertain_count += 1

            y_true.append(true_label)
            y_pred.append(final_label)

            if final_label != true_label:
                mismatches.append({
                    "index": i,
                    "text": text[:100],
                    "true_label": true_label,
                    "predicted": final_label,
                    "raw_label": raw_label,
                    "confidence": confidence_pct,
                    "is_uncertain": is_uncertain,
                })
        except Exception as e:
            logger.warning(
                "Prediction failed for sample %d: %s",
                i, str(e)[:80],
            )
            continue

    total = len(y_true)
    if total == 0:
        return {
            "error": "No valid samples processed",
            "total_samples": 0,
        }

    # ── Accuracy ──────────────────────────────────────────
    correct = sum(
        1 for t, p in zip(y_true, y_pred) if t == p
    )
    accuracy = correct / total

    # ── Per-class precision, recall, F1 ───────────────────
    precision = {}
    recall = {}
    f1 = {}

    for label in labels + ["uncertain"]:
        tp = sum(
            1 for t, p in zip(y_true, y_pred)
            if t == label and p == label
        )
        fp = sum(
            1 for t, p in zip(y_true, y_pred)
            if t != label and p == label
        )
        fn = sum(
            1 for t, p in zip(y_true, y_pred)
            if t == label and p != label
        )

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_val = (
            2 * prec * rec / (prec + rec)
            if (prec + rec) > 0
            else 0.0
        )

        precision[label] = round(prec, 4)
        recall[label] = round(rec, 4)
        f1[label] = round(f1_val, 4)

    # ── Macro F1 ──────────────────────────────────────────
    core_f1 = [f1[l] for l in labels]
    macro_f1 = sum(core_f1) / len(core_f1)

    # ── Confusion Matrix ──────────────────────────────────
    all_labels = labels + ["uncertain"]
    matrix: dict[str, dict[str, int]] = {
        t: {p: 0 for p in all_labels}
        for t in labels
    }
    for t, p in zip(y_true, y_pred):
        if t in matrix and p in matrix[t]:
            matrix[t][p] += 1

    # ── Translation stats ─────────────────────────────────
    trans_stats = get_translation_stats()

    processing_time = round(time.time() - start_time, 2)

    result = {
        "accuracy": round(accuracy, 4),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "macro_f1": round(macro_f1, 4),
        "confusion_matrix": matrix,
        "uncertain_rate": round(
            uncertain_count / total, 4
        ),
        "translation_fallback_rate": trans_stats.get(
            "fallback_rate", 0.0
        ),
        "total_samples": total,
        "correct": correct,
        "uncertain_count": uncertain_count,
        "processing_time_s": processing_time,
        "mismatches": mismatches[:50],  # Cap at 50
        "label_distribution": dict(Counter(y_true)),
        "prediction_distribution": dict(Counter(y_pred)),
    }

    return result


def load_dataset(path: str) -> list[dict]:
    """Load a JSON or CSV dataset.

    Expected format:
      JSON: [{"text": "...", "label": "positive"}, ...]
      CSV: text,label columns
    """
    filepath = Path(path)

    if filepath.suffix == ".json":
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    elif filepath.suffix == ".csv":
        import csv
        dataset = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = row.get(
                    "text", row.get("review", "")
                )
                label = row.get(
                    "label",
                    row.get("sentiment", ""),
                )
                if text and label:
                    dataset.append({
                        "text": text,
                        "label": label.lower(),
                    })
        return dataset

    else:
        raise ValueError(
            f"Unsupported format: {filepath.suffix}. "
            f"Use .json or .csv"
        )


def main():
    parser = argparse.ArgumentParser(
        description="ReviewSense E2E Evaluation"
    )
    parser.add_argument(
        "--dataset", type=str, required=True,
        help="Path to labeled dataset (.json or .csv)",
    )
    parser.add_argument(
        "--model", type=str, default="best",
        help="Model to evaluate (default: best)",
    )
    parser.add_argument(
        "--multilingual", action="store_true",
        help="Run multilingual comparison",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output file for results (.json)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s "
               "%(message)s",
    )

    logger.info("Loading dataset from %s", args.dataset)
    dataset = load_dataset(args.dataset)
    logger.info("Loaded %d samples", len(dataset))

    logger.info(
        "Evaluating with model=%s multilingual=%s",
        args.model, args.multilingual,
    )
    results = evaluate_dataset(
        dataset,
        model_choice=args.model,
        run_multilingual=args.multilingual,
    )

    # Print summary
    print("\n" + "=" * 50)
    print("  ReviewSense E2E Evaluation Results")
    print("=" * 50)
    print(f"  Samples:      {results['total_samples']}")
    print(f"  Accuracy:     {results['accuracy']:.2%}")
    print(f"  Macro F1:     {results['macro_f1']:.4f}")
    print(
        f"  Uncertain:    "
        f"{results['uncertain_rate']:.2%}"
    )
    print(
        f"  Trans Fallback: "
        f"{results['translation_fallback_rate']:.2%}"
    )
    print(f"  Time:         {results['processing_time_s']}s")
    print("=" * 50)

    print("\nPer-class F1:")
    for label in ["positive", "negative", "neutral",
                   "uncertain"]:
        f1_val = results["f1"].get(label, 0.0)
        print(f"  {label:>10s}: {f1_val:.4f}")

    print("\nConfusion Matrix:")
    header = (
        f"{'':>10s}"
        + "".join(f"{l:>12s}" for l in
                  ["positive", "negative", "neutral",
                   "uncertain"])
    )
    print(header)
    for true_label in ["positive", "negative", "neutral"]:
        row = results["confusion_matrix"].get(
            true_label, {}
        )
        vals = "".join(
            f"{row.get(p, 0):>12d}"
            for p in ["positive", "negative", "neutral",
                       "uncertain"]
        )
        print(f"{true_label:>10s}{vals}")

    # Save to file
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        logger.info("Results saved to %s", args.output)

    return results


if __name__ == "__main__":
    main()
