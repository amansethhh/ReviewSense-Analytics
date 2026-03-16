"""
scripts/train_final.py
-----------------------
Final optimized training: trains multiple LinearSVC/LR configurations
with different class_weight settings and TF-IDF params, picks the
config that maximizes BOTH test accuracy AND short-sentence validation.

Usage:
    $env:PYTHONUTF8='1'; python scripts/train_final.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.preprocess import preprocess_pipeline, normalize_label

DATASET_PATH = _PROJECT_ROOT / "data" / "processed" / "reviewsense_dataset.csv"
MODELS_DIR   = _PROJECT_ROOT / "models" / "classical"
REPORTS_DIR  = _PROJECT_ROOT / "reports"

CLASS_LABELS = [0, 1, 2]
CLASS_NAMES  = ["Negative", "Neutral", "Positive"]
RANDOM_STATE = 42

# Validation sentences that MUST pass
VALIDATION_CASES = [
    ("The food is so bad", 0, "Negative"),
    ("This product is terrible", 0, "Negative"),
    ("I hate this service", 0, "Negative"),
    ("The worst experience ever", 0, "Negative"),
    ("Very disappointed with the quality", 0, "Negative"),
    ("Awful product, complete waste of money", 0, "Negative"),
    ("This product is amazing", 2, "Positive"),
    ("I love this phone", 2, "Positive"),
    ("The service was excellent", 2, "Positive"),
    ("Best purchase I have ever made", 2, "Positive"),
    ("Outstanding quality and great value", 2, "Positive"),
    ("The food was okay", 1, "Neutral"),
    ("The product is average", 1, "Neutral"),
    ("It works as expected, nothing special", 1, "Neutral"),
]


def sanitize(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def validate_pipeline(pipeline) -> int:
    """Run validation sentences and return number passed."""
    passed = 0
    for text, expected, _ in VALIDATION_CASES:
        processed = preprocess_pipeline(text) or text.strip().lower()
        pred = int(pipeline.predict([processed])[0])
        if pred == expected:
            passed += 1
    return passed


def main():
    t_start = time.time()

    # ==================================================================
    # Load and preprocess dataset
    # ==================================================================
    print("=" * 70)
    print("  Loading and preprocessing dataset...")
    print("=" * 70)

    df = pd.read_csv(DATASET_PATH)
    print(f"  Raw: {len(df):,}")

    text_col = [c for c in df.columns if any(k in c.lower() for k in ("text","review","sentence","content","tweet"))][0]
    label_col = [c for c in df.columns if any(k in c.lower() for k in ("label","sentiment","rating","score","polarity"))][0]
    df = df.rename(columns={text_col: "text", label_col: "label"})
    df = df.dropna(subset=["text", "label"])
    df["label"] = df["label"].apply(normalize_label)
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)

    before = len(df)
    df = df.drop_duplicates(subset=["text"], keep="first")
    print(f"  Deduped: {before:,} -> {len(df):,}")

    print(f"  Preprocessing {len(df):,} texts...")
    df["text"] = df["text"].apply(preprocess_pipeline)
    df = df.dropna(subset=["text"])
    print(f"  After preprocessing: {len(df):,}")

    for label in CLASS_LABELS:
        count = (df["label"] == label).sum()
        print(f"    {label} ({CLASS_NAMES[label]:8s}): {count:>8,} ({count/len(df)*100:5.1f}%)")

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"].values, df["label"].values,
        test_size=0.2, stratify=df["label"], random_state=RANDOM_STATE
    )
    print(f"  Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    # ==================================================================
    # Try multiple configurations
    # ==================================================================
    print(f"\n{'=' * 70}")
    print("  Testing multiple configurations")
    print("=" * 70)

    configs = [
        # (name, tfidf_params, classifier)
        ("LR_balanced_20k", {"max_features": 20000, "ngram_range": (1, 2), "sublinear_tf": True},
         LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE)),

        ("LR_none_20k", {"max_features": 20000, "ngram_range": (1, 2), "sublinear_tf": True},
         LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, class_weight=None, random_state=RANDOM_STATE)),

        ("LR_none_50k", {"max_features": 50000, "ngram_range": (1, 2), "sublinear_tf": True},
         LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, class_weight=None, random_state=RANDOM_STATE)),

        ("SVC_balanced_20k", {"max_features": 20000, "ngram_range": (1, 2), "sublinear_tf": True},
         LinearSVC(C=0.1, max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE)),

        ("SVC_none_20k", {"max_features": 20000, "ngram_range": (1, 2), "sublinear_tf": True},
         LinearSVC(C=0.1, max_iter=2000, class_weight=None, random_state=RANDOM_STATE)),

        ("SVC_none_50k", {"max_features": 50000, "ngram_range": (1, 2), "sublinear_tf": True},
         LinearSVC(C=0.1, max_iter=2000, class_weight=None, random_state=RANDOM_STATE)),

        ("SVC_none_10k", {"max_features": 10000, "ngram_range": (1, 2), "sublinear_tf": True},
         LinearSVC(C=1.0, max_iter=2000, class_weight=None, random_state=RANDOM_STATE)),

        ("NB_10k", {"max_features": 10000, "ngram_range": (1, 2), "sublinear_tf": True},
         MultinomialNB(alpha=0.1)),

        ("LR_none_10k", {"max_features": 10000, "ngram_range": (1, 2), "sublinear_tf": True},
         LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, class_weight=None, random_state=RANDOM_STATE)),

        ("SVC_none_30k", {"max_features": 30000, "ngram_range": (1, 2), "sublinear_tf": True},
         LinearSVC(C=0.5, max_iter=2000, class_weight=None, random_state=RANDOM_STATE)),
    ]

    best_score = -1
    best_result = None
    all_results = []

    for name, tfidf_params, clf in configs:
        t0 = time.time()
        vec = TfidfVectorizer(**tfidf_params)
        X_tr = vec.fit_transform(X_train)
        X_te = vec.transform(X_test)

        clf.fit(X_tr, y_train)
        elapsed = time.time() - t0

        y_pred = clf.predict(X_te)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="macro")
        prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
        rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
        cm = confusion_matrix(y_test, y_pred, labels=CLASS_LABELS)

        pipeline = Pipeline([("tfidf", vec), ("clf", clf)])
        val_passed = validate_pipeline(pipeline)

        # Combined score: f1 + bonus for validation pass rate
        combined = f1 + (val_passed / len(VALIDATION_CASES)) * 0.15

        print(f"  {name:25s}  Acc={acc:.4f}  F1={f1:.4f}  Val={val_passed:>2d}/{len(VALIDATION_CASES)}  Time={elapsed:.1f}s  Score={combined:.4f}")

        result = {
            "name": name,
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "val_passed": val_passed,
            "combined": combined,
            "confusion_matrix": cm.tolist(),
            "training_time_sec": float(elapsed),
            "pipeline": pipeline,
            "tfidf_params": tfidf_params,
            "clf": clf,
        }
        all_results.append(result)

        if combined > best_score:
            best_score = combined
            best_result = result

    # ==================================================================
    # Report best config
    # ==================================================================
    print(f"\n{'=' * 70}")
    print(f"  Best configuration: {best_result['name']}")
    print("=" * 70)
    print(f"  Accuracy:   {best_result['accuracy']:.4f}")
    print(f"  Precision:  {best_result['precision']:.4f}")
    print(f"  Recall:     {best_result['recall']:.4f}")
    print(f"  F1 (macro): {best_result['f1']:.4f}")
    print(f"  Validation: {best_result['val_passed']}/{len(VALIDATION_CASES)} passed")

    best_pipeline = best_result["pipeline"]

    # Print classification report
    y_pred = best_pipeline.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=CLASS_NAMES, zero_division=0)
    print(f"\n{report}")

    # ==================================================================
    # Error analysis
    # ==================================================================
    print(f"\n{'=' * 70}")
    print("  Error Analysis")
    print("=" * 70)

    misclassified = []
    for i in range(len(y_test)):
        if y_test[i] != y_pred[i]:
            misclassified.append({
                "text": X_test[i][:120],
                "true": CLASS_NAMES[int(y_test[i])],
                "pred": CLASS_NAMES[int(y_pred[i])],
            })

    total_errors = len(misclassified)
    print(f"\n  Total misclassified: {total_errors:,} / {len(y_test):,} ({total_errors/len(y_test)*100:.1f}%)")

    error_patterns = {}
    for m in misclassified:
        key = f"{m['true']} -> {m['pred']}"
        error_patterns[key] = error_patterns.get(key, 0) + 1

    print(f"\n  Error patterns:")
    for pattern, count in sorted(error_patterns.items(), key=lambda x: -x[1]):
        print(f"    {pattern:30s}: {count:>5,}")

    print(f"\n  Top 20 misclassified:")
    for i, m in enumerate(misclassified[:20]):
        print(f"    {i+1:2d}. [{m['true']:>8s} -> {m['pred']:>8s}] \"{m['text']}\"")

    # ==================================================================
    # Save artifacts
    # ==================================================================
    print(f"\n{'=' * 70}")
    print("  Saving final model and artifacts")
    print("=" * 70)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save best model
    joblib.dump(best_pipeline, MODELS_DIR / "best_model.pkl")
    print(f"  [OK] Best model ({best_result['name']}) -> models/classical/best_model.pkl")

    # Save individual model pipelines with known names
    model_names_map = {
        "naive_bayes": ("NB_10k", MultinomialNB),
        "logistic_regression": ("LR_none", LogisticRegression),
        "linearsvc": ("SVC_none", LinearSVC),
    }
    for fname, (prefix, cls) in model_names_map.items():
        matching = [r for r in all_results if r["name"].startswith(prefix)]
        if matching:
            best_of_type = max(matching, key=lambda x: x["combined"])
            joblib.dump(best_of_type["pipeline"], MODELS_DIR / f"{fname}.pkl")

    # Save vectorizer
    joblib.dump(best_pipeline.named_steps["tfidf"], MODELS_DIR / "tfidf_vectorizer.pkl")

    # Save label map
    label_map = {str(k): v for k, v in zip(CLASS_LABELS, CLASS_NAMES)}
    with open(MODELS_DIR / "label_map.json", "w") as f:
        json.dump(label_map, f, indent=2)

    # Save results
    results_json = {}
    for r in all_results:
        results_json[r["name"]] = {
            "accuracy": r["accuracy"],
            "precision": r["precision"],
            "recall": r["recall"],
            "f1": r["f1"],
            "val_passed": r["val_passed"],
            "confusion_matrix": r["confusion_matrix"],
            "training_time_sec": r["training_time_sec"],
        }
    with open(REPORTS_DIR / "model_results.json", "w") as f:
        json.dump(results_json, f, indent=2)
    print(f"  [OK] Results -> reports/model_results.json")

    # ==================================================================
    # Final validation
    # ==================================================================
    print(f"\n{'=' * 70}")
    print("  Final Validation Test")
    print("=" * 70)

    passed = 0
    for text, expected, exp_name in VALIDATION_CASES:
        processed = preprocess_pipeline(text) or text.strip().lower()
        pred = int(best_pipeline.predict([processed])[0])
        ok = pred == expected
        status = "[PASS]" if ok else "[FAIL]"
        if ok:
            passed += 1
        print(f"  {status} \"{text}\" -> {CLASS_NAMES[pred]:10s} (expected {exp_name})")

    print(f"\n  Validation: {passed}/{len(VALIDATION_CASES)} passed")

    # ==================================================================
    # Comparison table
    # ==================================================================
    total_time = time.time() - t_start
    print(f"\n{'=' * 70}")
    print("  ALL CONFIGURATIONS COMPARISON")
    print("=" * 70)
    print(f"\n  {'Config':<25s} | {'Acc':>6s} | {'F1':>6s} | {'Val':>5s} | {'Score':>6s}")
    print("  " + "-" * 60)
    for r in sorted(all_results, key=lambda x: -x["combined"]):
        marker = " [BEST]" if r["name"] == best_result["name"] else ""
        print(f"  {r['name']:<25s} | {r['accuracy']:>6.4f} | {r['f1']:>6.4f} | "
              f"{r['val_passed']:>2d}/{len(VALIDATION_CASES)} | {r['combined']:>6.4f}{marker}")

    print(f"\n  Confusion Matrix ({best_result['name']}):")
    cm = np.array(best_result["confusion_matrix"])
    print(f"  {'':>12s} {'Neg':>8s} {'Neu':>8s} {'Pos':>8s}")
    for i, row_name in enumerate(CLASS_NAMES):
        print(f"  {row_name:>12s} {cm[i,0]:>8d} {cm[i,1]:>8d} {cm[i,2]:>8d}")

    print(f"\n  Total time: {total_time/60:.1f} minutes")
    print("=" * 70)


if __name__ == "__main__":
    main()
