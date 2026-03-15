"""
scripts/generate_demo_artifacts.py
-----------------------------------
Generates demo model artifacts so the Streamlit dashboard can run end-to-end
without the full 1.3M-row production dataset.

Run this script once before launching the app:

    python scripts/generate_demo_artifacts.py

It creates:
    models/classical/best_model.pkl
    models/classical/tfidf_vectorizer.pkl
    reports/model_results.json

The demo models are trained on a small built-in sample corpus (90 labelled
reviews) and are suitable for UI demonstration only.  For production accuracy
use the full dataset + src/train_classical.py instead.
"""

from __future__ import annotations

import json
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
from sklearn.metrics import accuracy_score, auc, confusion_matrix, f1_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import label_binarize
from sklearn.svm import LinearSVC

import joblib

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
]

_CLASS_LABELS = [0, 1, 2]


def _compute_roc(model, X_vec, y_test: list[int]) -> dict | None:
    """Compute micro-average OvR ROC data for a fitted model."""
    try:
        y_bin = label_binarize(y_test, classes=_CLASS_LABELS)
        if hasattr(model, "predict_proba"):
            scores = np.asarray(model.predict_proba(X_vec))
        elif hasattr(model, "decision_function"):
            raw = np.asarray(model.decision_function(X_vec))
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

    texts = [t for t, _ in _DEMO_CORPUS]
    labels = [lbl for _, lbl in _DEMO_CORPUS]

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )

    print(f"\nTrain size: {len(X_train)}  |  Test size: {len(X_test)}")

    # ── TF-IDF vectoriser ──────────────────────────────────────────────────
    vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # ── Model zoo ─────────────────────────────────────────────────────────
    _MODELS: dict[str, Any] = {
        "Naive Bayes": MultinomialNB(),
        "LinearSVC": LinearSVC(random_state=42, max_iter=1000),
        "Logistic Regression": LogisticRegression(random_state=42, max_iter=500),
        "Random Forest": RandomForestClassifier(n_estimators=50, random_state=42),
    }

    results: dict[str, dict[str, Any]] = {}
    best_f1 = -1.0
    best_model = None
    best_name = ""

    print("\nTraining models…\n")

    for name, model in _MODELS.items():
        t0 = time.time()
        model.fit(X_train_vec, y_train)
        elapsed = time.time() - t0

        y_pred = model.predict(X_test_vec)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="macro")
        cm = confusion_matrix(y_test, y_pred, labels=_CLASS_LABELS)

        metrics: dict[str, Any] = {
            "accuracy": float(acc),
            "f1": float(f1),
            "confusion_matrix": cm.tolist(),
            "training_time_sec": float(elapsed),
        }

        roc = _compute_roc(model, X_test_vec, y_test)
        if roc is not None:
            metrics["roc"] = roc

        results[name] = metrics
        print(f"  {name:25s}  acc={acc:.3f}  macro-f1={f1:.3f}")

        if f1 > best_f1:
            best_f1 = f1
            best_model = model
            best_name = name

    # ── Save TF-IDF vectoriser ─────────────────────────────────────────────
    models_dir = _PROJECT_ROOT / "models" / "classical"
    models_dir.mkdir(parents=True, exist_ok=True)

    vec_path = models_dir / "tfidf_vectorizer.pkl"
    joblib.dump(vectorizer, vec_path)
    print(f"\n✓ Saved vectoriser → {vec_path.relative_to(_PROJECT_ROOT)}")

    # ── Save best model as a full Pipeline ────────────────────────────────
    best_pipeline = Pipeline([("tfidf", vectorizer), ("clf", best_model)])
    model_path = models_dir / "best_model.pkl"
    joblib.dump(best_pipeline, model_path)
    print(f"✓ Saved best model ({best_name}) → {model_path.relative_to(_PROJECT_ROOT)}")

    # ── Save model_results.json ───────────────────────────────────────────
    reports_dir = _PROJECT_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    results_path = reports_dir / "model_results.json"
    with open(results_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"✓ Saved metrics      → {results_path.relative_to(_PROJECT_ROOT)}")

    print("\n" + "=" * 60)
    print("Done!  Launch the dashboard with:")
    print("    streamlit run app/app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
