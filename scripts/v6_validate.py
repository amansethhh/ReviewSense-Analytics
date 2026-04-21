"""V6 multilingual validation runner.

Runs translation spot checks, multilingual sentiment accuracy, confusion
matrix, error cases, and raw single/batch consistency.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

LABELS = ["positive", "negative", "neutral"]

TRANSLATION_CASES = [
    {"lang": "hi", "text": "यह उत्पाद बहुत अच्छा है"},
    {"lang": "fr", "text": "Ce produit est excellent."},
    {"lang": "ar", "text": "هذا المنتج ممتاز."},
    {"lang": "ja", "text": "この製品は素晴らしいです。"},
]

SENTIMENT_CASES = [
    {"lang": "en", "text": "This product is excellent and I love it.", "label": "positive"},
    {"lang": "en", "text": "This product is terrible and completely broken.", "label": "negative"},
    {"lang": "en", "text": "It works as expected, nothing special.", "label": "neutral"},
    {"lang": "hi", "text": "यह उत्पाद बहुत अच्छा है", "label": "positive"},
    {"lang": "hi", "text": "यह उत्पाद बहुत खराब है", "label": "negative"},
    {"lang": "fr", "text": "Ce produit est excellent.", "label": "positive"},
    {"lang": "fr", "text": "Ce produit est terrible.", "label": "negative"},
    {"lang": "de", "text": "Dieses Produkt ist ausgezeichnet.", "label": "positive"},
    {"lang": "de", "text": "Dieses Produkt ist schrecklich.", "label": "negative"},
    {"lang": "ar", "text": "هذا المنتج ممتاز.", "label": "positive"},
    {"lang": "ar", "text": "هذا المنتج سيء جدا.", "label": "negative"},
    {"lang": "ja", "text": "この製品は素晴らしいです。", "label": "positive"},
    {"lang": "ja", "text": "この製品は最悪です。", "label": "negative"},
]


def _empty_confusion() -> dict[str, dict[str, int]]:
    return {true: {pred: 0 for pred in LABELS} for true in LABELS}


def main() -> int:
    from src.models.sentiment import predict as raw_predict
    from src.models.sentiment import predict_batch as raw_predict_batch
    from src.models.translation import translate_to_english, validate_translation
    from src.pipeline.inference import run_pipeline_batch
    from src.predict import predict_sentiment
    from backend.app.routes.language import detect_translate_and_predict_sync

    started = time.perf_counter()

    translations = []
    for case in TRANSLATION_CASES:
        translated, method = translate_to_english(case["text"], case["lang"])
        translations.append({
            **case,
            "translation": translated,
            "method": method,
            "valid": validate_translation(case["text"], translated),
        })

    y_true: list[str] = []
    y_pred: list[str] = []
    errors = []
    samples = []

    for case in SENTIMENT_CASES:
        pred = predict_sentiment(
            case["text"],
            case["lang"],
            run_sarcasm_detection=False,
        )
        label = str(pred.get("label_name", "neutral")).lower()
        if label not in LABELS:
            label = "neutral"
        confidence = round(float(pred.get("confidence", 0.0)) * 100, 2)
        y_true.append(case["label"])
        y_pred.append(label)
        row = {
            **case,
            "prediction": label,
            "confidence": confidence,
            "model_used": pred.get("model_used"),
        }
        samples.append(row)
        if label != case["label"]:
            errors.append(row)

    confusion = _empty_confusion()
    for true, pred in zip(y_true, y_pred):
        confusion[true][pred] += 1

    correct = sum(t == p for t, p in zip(y_true, y_pred))
    accuracy = correct / len(y_true) if y_true else 0.0

    raw_single = [
        raw_predict(case["text"], lang_code=case["lang"])
        for case in SENTIMENT_CASES
    ]
    raw_batch = raw_predict_batch(
        [case["text"] for case in SENTIMENT_CASES],
        lang_codes=[case["lang"] for case in SENTIMENT_CASES],
    )
    consistency_errors = []
    for idx, (single, batch) in enumerate(zip(raw_single, raw_batch)):
        if (
            single["label_name"] != batch["label_name"]
            or abs(single["confidence"] - batch["confidence"]) >= 0.01
        ):
            consistency_errors.append({
                "index": idx,
                "text": SENTIMENT_CASES[idx]["text"],
                "single": single,
                "batch": batch,
            })

    bulk_outputs = run_pipeline_batch(
        [case["text"] for case in SENTIMENT_CASES],
        enable_sarcasm=False,
        enable_aspects=False,
    )
    mode_consistency_errors = []
    for idx, (case, live_label, bulk_row) in enumerate(
        zip(SENTIMENT_CASES, y_pred, bulk_outputs)
    ):
        bulk_label = str(
            bulk_row.get("label_name")
            or bulk_row.get("sentiment")
            or "neutral"
        ).lower()
        multilingual = detect_translate_and_predict_sync(
            case["text"],
            multilingual=True,
            run_absa=False,
            run_sarcasm=False,
        )
        multilingual_label = str(
            multilingual.get("sentiment", "neutral")
        ).lower()
        if len({live_label, bulk_label, multilingual_label}) != 1:
            mode_consistency_errors.append({
                "index": idx,
                "lang": case["lang"],
                "text": case["text"],
                "live": live_label,
                "bulk": bulk_label,
                "multilingual": multilingual_label,
            })

    elapsed = time.perf_counter() - started
    report = {
        "accuracy": round(accuracy, 4),
        "accuracy_pct": round(accuracy * 100, 2),
        "total": len(y_true),
        "correct": correct,
        "confusion_matrix": confusion,
        "error_cases": errors,
        "translations": translations,
        "sample_outputs": samples[:8],
        "batch_consistency_errors": consistency_errors,
        "mode_consistency_errors": mode_consistency_errors,
        "processing_time_s": round(elapsed, 3),
        "avg_ms_per_sample": round(elapsed * 1000 / max(len(SENTIMENT_CASES), 1), 2),
    }

    out_path = ROOT / "reports" / "v6_validation_results.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if not errors and not consistency_errors and not mode_consistency_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
