"""
scripts/generate_demo_artifacts.py
-----------------------------------
Generates demo model artifacts so the Streamlit dashboard can run end-to-end
without the full 1.3M-row production dataset.

Run this script once before launching the app:

    python scripts/generate_demo_artifacts.py

It creates:
    models/classical/best_model.pkl          (full Pipeline)
    models/classical/tfidf_vectorizer.pkl
    models/classical/naive_bayes.pkl         (full Pipeline)
    models/classical/linearsvc.pkl           (full Pipeline)
    models/classical/logistic_regression.pkl (full Pipeline)
    models/classical/random_forest.pkl       (full Pipeline)
    models/classical/label_map.json
    reports/model_results.json

The demo models are trained on a small built-in sample corpus (90 labelled
reviews) and are suitable for UI demonstration only.  For production accuracy
use the full dataset + src/train_classical.py instead.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Resolve project root so we can import src modules
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    auc,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import label_binarize
from sklearn.svm import LinearSVC

import joblib

from src.preprocess import preprocess_pipeline

# ---------------------------------------------------------------------------
# Embedded demo corpus  (label: 0=Negative, 1=Neutral, 2=Positive)
# ---------------------------------------------------------------------------
_DEMO_CORPUS: list[tuple[str, int]] = [
    # --- Positive (label=2) ---
    ("The product is absolutely amazing and exceeded my expectations!", 2),
    ("Great quality, fast shipping — highly recommend this product.", 2),
    ("Best purchase I have made in years. Very satisfied!", 2),
    ("Excellent customer service and top-notch product quality.", 2),
    ("This is perfect and works exactly as described.", 2),
    ("Outstanding product! Will definitely buy again.", 2),
    ("Fantastic product, great value for money.", 2),
    ("I love this product. Works perfectly and looks great!", 2),
    ("Super happy with this purchase. Highly recommended.", 2),
    ("The quality is top notch and delivery was incredibly fast.", 2),
    ("Brilliant! Highly satisfied with the purchase.", 2),
    ("Works like a charm. Very happy with the result.", 2),
    ("Exceeded all expectations. Will recommend to friends.", 2),
    ("Amazing value for the price. Five stars all the way!", 2),
    ("The best product I have ever used. Absolutely love it.", 2),
    ("Incredible product. Does everything promised.", 2),
    ("Very pleased with this purchase. Would definitely buy again.", 2),
    ("Great product at an affordable price. Happy customer!", 2),
    ("Wonderful experience, the product is exactly what I needed.", 2),
    ("Perfect in every way. Highly delighted with this product.", 2),
    ("Superb quality and fast delivery. Highly recommend.", 2),
    ("The item arrived on time and in perfect condition.", 2),
    ("Brilliant! The best thing I have bought this year.", 2),
    ("Really excellent product and great customer support.", 2),
    ("Love the design and functionality of this product.", 2),
    ("Five-star product! Absolutely delighted.", 2),
    ("Simply the best. Exceptional quality and service.", 2),
    ("Could not be happier with this purchase.", 2),
    ("The product works great and looks even better than expected.", 2),
    ("One of the best products I have ever bought. Superb!", 2),
    ("The food was delicious and the service was outstanding.", 2),
    ("I love this phone. The camera is amazing and battery lasts forever.", 2),
    ("This service was excellent. Prompt and professional.", 2),
    ("Truly remarkable product, exceeded every expectation I had.", 2),
    ("The quality is superb and shipping was incredibly fast.", 2),
    ("A wonderful product that brings joy every day.", 2),
    ("Hands down the best gadget I have purchased this year.", 2),
    ("I am thoroughly impressed by the build quality and design.", 2),
    ("An excellent phone with wonderful features and great battery.", 2),
    ("Delightful shopping experience, will definitely come back.", 2),
    ("The food was amazing, perfectly cooked and beautifully presented.", 2),
    ("I am so happy with this product, it works exactly as promised.", 2),
    ("This product is brilliant, good quality, and great design.", 2),
    ("My experience with customer support was great and helpful.", 2),
    ("Fabulous product, love everything about this purchase.", 2),
    # --- Negative (label=0) ---
    ("Terrible product, broke after just two days of use.", 0),
    ("Worst purchase ever. Complete waste of money.", 0),
    ("Very disappointed with the quality. Will not buy again.", 0),
    ("The product is awful and customer service is terrible.", 0),
    ("Do not buy this. It is a complete scam.", 0),
    ("Poor quality, fell apart within a week. Very disappointing.", 0),
    ("I hate this product. It does not work at all.", 0),
    ("Broken on arrival. Terrible packaging and quality control.", 0),
    ("Absolutely horrible experience. Never buying from this seller again.", 0),
    ("Garbage product. Total waste of money and time.", 0),
    ("The worst product I have ever purchased. Very bad.", 0),
    ("Failed after one use. Complete garbage. Would not recommend.", 0),
    ("The product is defective and the seller is totally unresponsive.", 0),
    ("Very poor build quality. Not worth the price at all.", 0),
    ("Awful product. Instructions make no sense and it does not work.", 0),
    ("Completely useless and very low quality. Avoid at all costs!", 0),
    ("Disappointed with the quality. Does not match the description.", 0),
    ("Never received my order. Terrible customer service experience.", 0),
    ("The item broke immediately. Very poor craftsmanship.", 0),
    ("Absolutely terrible. Not as advertised. Complete waste of money.", 0),
    ("Such a bad product. Stopped working after just one day.", 0),
    ("Horrible quality. The item was already damaged when delivered.", 0),
    ("Not worth a single star. Completely broken and useless.", 0),
    ("The worst purchase of my life. Complete junk.", 0),
    ("Very bad product. Nothing works as advertised.", 0),
    ("Terrible quality and extremely poor customer service.", 0),
    ("This product is a scam. Does not work as described.", 0),
    ("Extremely disappointed. Would not recommend to anyone.", 0),
    ("Avoid this product at all costs. Complete waste of money.", 0),
    ("Very low quality product. Broke after just one use.", 0),
    ("The food is so bad and I will never come back.", 0),
    ("I hate this service. Truly awful experience overall.", 0),
    ("The worst experience ever. Completely unacceptable.", 0),
    ("This product is terrible. Completely disappointed.", 0),
    ("This is horrible and not worth any money at all.", 0),
    ("Terrible phone. The screen broke within one week of usage.", 0),
    ("The food was terrible and made me feel sick afterwards.", 0),
    ("I am so sad and disappointed with this terrible product.", 0),
    ("Horrible service, rude staff, and terrible food quality.", 0),
    ("This product is absolutely terrible, worst I have ever tried.", 0),
    ("Terrible experience with this company, never coming back.", 0),
    ("The product is horrible, poor quality, and bad design.", 0),
    ("Dreadful product. Stopped working after the first charge.", 0),
    ("This was a horrible purchase. I regret every penny.", 0),
    ("The worst meal I have ever had, food was disgusting.", 0),
    ("Service was terrible and the product is even worse.", 0),
    ("Hate everything about this product, total disappointment.", 0),
    ("Bad quality, bad service, bad experience overall.", 0),
    ("Pathetic product. Falls apart if you even look at it.", 0),
    # --- Neutral (label=1) ---
    ("The product is okay. Not great but not terrible either.", 1),
    ("It works as expected. Nothing special about it.", 1),
    ("Average product. Does the job but could definitely be better.", 1),
    ("Decent quality for the price. Not the best but acceptable.", 1),
    ("Product is fine. Met my basic expectations.", 1),
    ("It is okay. Nothing to write home about.", 1),
    ("Mediocre product. Gets the job done but just barely.", 1),
    ("Average product. Some features work, some do not.", 1),
    ("Neither good nor bad. Just an average product overall.", 1),
    ("The product does what it says. Nothing more, nothing less.", 1),
    ("It is acceptable. Not particularly impressed but not disappointed.", 1),
    ("Fair product for the price. Average quality overall.", 1),
    ("The product is adequate. Meets minimum requirements.", 1),
    ("So-so product. Has some pros and some cons.", 1),
    ("Average quality. Works sometimes but not consistently.", 1),
    ("Not bad, not great. Just a regular average product.", 1),
    ("Product is functional. Basic but does its job.", 1),
    ("Reasonable product for the price. Average experience overall.", 1),
    ("Okay product. Has some issues but generally works.", 1),
    ("Moderate quality. Not what I hoped for but usable.", 1),
    ("Standard product. Does what it is supposed to do.", 1),
    ("The item is acceptable. Nothing exceptional here.", 1),
    ("Satisfactory product. No major complaints but no praise either.", 1),
    ("The product performs adequately. Average overall.", 1),
    ("It is a basic product. Meets standard expectations.", 1),
    ("Neutral experience. The product is neither great nor terrible.", 1),
    ("An okay purchase. Serves its purpose adequately.", 1),
    ("Reasonable product. Would work for basic needs.", 1),
    ("Product is fine. Has both good and bad aspects.", 1),
    ("Decent enough. Not the best, but not the worst either.", 1),
    ("The food was okay. Nothing special but edible.", 1),
    ("The product is average. Works as expected.", 1),
    ("The phone works but nothing to brag about.", 1),
    ("Service was passable. Did not exceed or fall below expectations.", 1),
    ("An ordinary item that does its job adequately.", 1),
    ("The food was fine. Not amazing but okay for the price.", 1),
    ("The food was alright. A bit bland but okay overall.", 1),
    ("Food was okay, not the best but decent enough to eat.", 1),
    ("The food was okay and the restaurant was clean.", 1),
    ("Average food. Nothing wrong but nothing special either.", 1),
    ("The meal was okay. Edible but not memorable.", 1),
    ("Service was okay. Staff was friendly but slow.", 1),
    ("Not bad food. Portion size was acceptable.", 1),
]

_CLASS_LABELS = [0, 1, 2]
_CLASS_NAMES = ["Negative", "Neutral", "Positive"]


def _sanitize_model_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _compute_roc(pipeline, X_test, y_test: list[int]) -> dict | None:
    """Compute micro-average OvR ROC data for a fitted pipeline."""
    try:
        y_bin = label_binarize(y_test, classes=_CLASS_LABELS)

        if hasattr(pipeline, "predict_proba"):
            scores = np.asarray(pipeline.predict_proba(X_test))
        elif hasattr(pipeline, "decision_function"):
            raw = np.asarray(pipeline.decision_function(X_test))
            if raw.ndim == 1:
                raw = raw.reshape(-1, 1)
            shifted = raw - raw.max(axis=1, keepdims=True)
            exp_raw = np.exp(shifted)
            scores = exp_raw / exp_raw.sum(axis=1, keepdims=True)
        else:
            return None

        fpr, tpr, _ = roc_curve(y_bin.ravel(), scores.ravel())
        roc_auc = float(auc(fpr, tpr))
        step = max(1, len(fpr) // 300)
        return {
            "fpr": fpr[::step].tolist(),
            "tpr": tpr[::step].tolist(),
            "auc": roc_auc,
        }
    except Exception as exc:
        print(f"    [ROC] skipped: {exc}")
        return None


def main() -> None:
    print("=" * 60)
    print("ReviewSense — demo artifact generator")
    print("=" * 60)

    # ── CRITICAL FIX: Preprocess all texts identically to inference ────────
    raw_texts = [t for t, _ in _DEMO_CORPUS]
    labels = [lbl for _, lbl in _DEMO_CORPUS]

    print("\nPreprocessing demo corpus...")
    processed_texts = []
    processed_labels = []
    for text, label in zip(raw_texts, labels):
        processed = preprocess_pipeline(text)
        if processed:
            processed_texts.append(processed)
            processed_labels.append(label)
        else:
            # Fallback: use lowercase text if preprocessing yields nothing
            processed_texts.append(text.strip().lower())
            processed_labels.append(label)

    print(f"  Preprocessed {len(processed_texts)} samples")

    X_train, X_test, y_train, y_test = train_test_split(
        processed_texts, processed_labels,
        test_size=0.25, random_state=42, stratify=processed_labels,
    )

    print(f"\nTrain size: {len(X_train)}  |  Test size: {len(X_test)}")

    # ── TF-IDF vectoriser ──────────────────────────────────────────────────
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))

    # ── Model zoo ─────────────────────────────────────────────────────────
    _MODELS: dict[str, Any] = {
        "Naive Bayes": MultinomialNB(),
        "LinearSVC": LinearSVC(random_state=42, max_iter=2000),
        "Logistic Regression": LogisticRegression(random_state=42, max_iter=1000, C=1.0),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    }

    results: dict[str, dict[str, Any]] = {}
    best_f1 = -1.0
    best_pipeline = None
    best_name = ""

    models_dir = _PROJECT_ROOT / "models" / "classical"
    models_dir.mkdir(parents=True, exist_ok=True)

    print("\nTraining models…\n")

    for name, model in _MODELS.items():
        t0 = time.time()

        # Create full Pipeline for each model
        pipeline = Pipeline([
            ("tfidf", vectorizer),
            ("clf", model),
        ])
        pipeline.fit(X_train, y_train)
        elapsed = time.time() - t0

        y_pred = pipeline.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="macro")
        prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
        rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
        cm = confusion_matrix(y_test, y_pred, labels=_CLASS_LABELS)

        report = classification_report(
            y_test, y_pred.tolist() if hasattr(y_pred, 'tolist') else y_pred,
            target_names=_CLASS_NAMES,
            zero_division=0,
        )

        metrics: dict[str, Any] = {
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "confusion_matrix": cm.tolist(),
            "training_time_sec": float(elapsed),
        }

        roc = _compute_roc(pipeline, X_test, y_test)
        if roc is not None:
            metrics["roc"] = roc

        results[name] = metrics
        print(f"  {name:25s}  acc={acc:.3f}  prec={prec:.3f}  recall={rec:.3f}  macro-f1={f1:.3f}")
        print(report)

        # Save each model as a FULL Pipeline
        model_file = models_dir / f"{_sanitize_model_name(name)}.pkl"
        joblib.dump(pipeline, model_file)
        print(f"    ✓ Saved → {model_file.relative_to(_PROJECT_ROOT)}")

        if f1 > best_f1:
            best_f1 = f1
            best_pipeline = pipeline
            best_name = name

    # ── Save TF-IDF vectoriser (backward compatibility) ───────────────────
    vec_path = models_dir / "tfidf_vectorizer.pkl"
    joblib.dump(vectorizer, vec_path)
    print(f"\n✓ Saved vectoriser → {vec_path.relative_to(_PROJECT_ROOT)}")

    # ── Save best model as a full Pipeline ────────────────────────────────
    model_path = models_dir / "best_model.pkl"
    joblib.dump(best_pipeline, model_path)
    print(f"✓ Saved best model ({best_name}) → {model_path.relative_to(_PROJECT_ROOT)}")

    # ── Save label map ────────────────────────────────────────────────────
    label_map = {0: "Negative", 1: "Neutral", 2: "Positive"}
    label_map_path = models_dir / "label_map.json"
    with open(label_map_path, "w", encoding="utf-8") as fh:
        json.dump(label_map, fh, indent=2)
    print(f"✓ Saved label map   → {label_map_path.relative_to(_PROJECT_ROOT)}")

    # ── Save model_results.json ───────────────────────────────────────────
    reports_dir = _PROJECT_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    results_path = reports_dir / "model_results.json"
    with open(results_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"✓ Saved metrics      → {results_path.relative_to(_PROJECT_ROOT)}")

    # ── Quick validation ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Quick validation on test sentences:")
    print("=" * 60)

    test_sentences = [
        ("The food is so bad", 0),
        ("This product is terrible", 0),
        ("I hate this service", 0),
        ("The worst experience ever", 0),
        ("This product is amazing", 2),
        ("I love this phone", 2),
        ("The service was excellent", 2),
        ("The food was okay", 1),
        ("The product is average", 1),
    ]

    label_names = {0: "Negative", 1: "Neutral", 2: "Positive"}
    correct = 0
    total = len(test_sentences)

    for text, expected_label in test_sentences:
        processed = preprocess_pipeline(text) or text.strip().lower()
        pred = best_pipeline.predict([processed])[0]
        pred_label = int(pred)
        status = "✅" if pred_label == expected_label else "❌"
        if pred_label == expected_label:
            correct += 1
        print(f"  {status} \"{text}\" → {label_names.get(pred_label, pred_label)} (expected {label_names.get(expected_label)})")

    print(f"\nValidation: {correct}/{total} correct")
    print("\n" + "=" * 60)
    print("Done!  Launch the dashboard with:")
    print("    streamlit run app/app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
