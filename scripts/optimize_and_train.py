"""
scripts/optimize_and_train.py
------------------------------
Full model training pipeline with:
  - Dataset deduplication
  - Class-balanced training
  - Hyperparameter optimization via GridSearchCV
  - Error analysis (top misclassified examples)
  - Saves all models as full sklearn Pipelines

Usage:
    python scripts/optimize_and_train.py
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
from sklearn.ensemble import RandomForestClassifier
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
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.preprocess import preprocess_pipeline, normalize_label

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────
DATASET_PATH = _PROJECT_ROOT / "data" / "processed" / "reviewsense_dataset.csv"
MODELS_DIR   = _PROJECT_ROOT / "models" / "classical"
REPORTS_DIR  = _PROJECT_ROOT / "reports"

CLASS_LABELS = [0, 1, 2]
CLASS_NAMES  = ["Negative", "Neutral", "Positive"]

RANDOM_STATE = 42
TEST_SIZE    = 0.2
SAMPLE_SIZE  = 300_000   # max rows to use (set None for all)

# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 — Load and clean dataset
# ──────────────────────────────────────────────────────────────────────────────
def load_dataset() -> pd.DataFrame:
    print("=" * 70)
    print("  STEP 1 — Loading and cleaning dataset")
    print("=" * 70)

    df = pd.read_csv(DATASET_PATH)
    print(f"\n  Raw rows: {len(df):,}")

    # Detect text/label columns
    text_col = [c for c in df.columns if any(k in c.lower() for k in ("text", "review", "sentence", "content", "tweet"))][0]
    label_col = [c for c in df.columns if any(k in c.lower() for k in ("label", "sentiment", "rating", "score", "polarity"))][0]
    print(f"  Text column: {text_col}")
    print(f"  Label column: {label_col}")

    df = df.rename(columns={text_col: "text", label_col: "label"})
    df = df.dropna(subset=["text", "label"])
    print(f"  After dropping nulls: {len(df):,}")

    # Normalize labels
    df["label"] = df["label"].apply(normalize_label)
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)

    # Remove duplicates
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["text"], keep="first")
    removed = before_dedup - len(df)
    print(f"  Removed {removed:,} duplicates → {len(df):,} unique")

    # Class distribution
    print(f"\n  Class distribution:")
    for label in CLASS_LABELS:
        count = (df["label"] == label).sum()
        pct = count / len(df) * 100
        print(f"    {label} ({CLASS_NAMES[label]:8s}): {count:>8,} ({pct:5.1f}%)")

    # Sample if needed
    if SAMPLE_SIZE and len(df) > SAMPLE_SIZE:
        df, _ = train_test_split(
            df, train_size=SAMPLE_SIZE, stratify=df["label"], random_state=RANDOM_STATE
        )
        print(f"  Sampled to {len(df):,} rows")

    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 — Preprocess text
# ──────────────────────────────────────────────────────────────────────────────
def preprocess_dataset(df: pd.DataFrame) -> pd.DataFrame:
    print(f"\n{'=' * 70}")
    print("  STEP 2 — Preprocessing text")
    print("=" * 70)

    total = len(df)
    processed = []
    batch_size = 10000

    for i in range(0, total, batch_size):
        batch = df.iloc[i:i+batch_size]
        results = batch["text"].apply(preprocess_pipeline)
        processed.append(results)
        done = min(i + batch_size, total)
        print(f"  Processed {done:>7,} / {total:,} ({done/total*100:.0f}%)", end="\r")

    df = df.copy()
    df["text"] = pd.concat(processed)
    print(f"  Processed {total:>7,} / {total:,} (100%)")

    # Drop rows where preprocessing returned None
    before = len(df)
    df = df.dropna(subset=["text"])
    dropped = before - len(df)
    print(f"  Dropped {dropped:,} empty rows after preprocessing → {len(df):,} remaining")

    # Text length stats after preprocessing
    df["text_len"] = df["text"].str.len()
    print(f"  Avg preprocessed text length: {df['text_len'].mean():.0f} chars")
    df = df.drop(columns=["text_len"])

    return df


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 — TF-IDF parameter search
# ──────────────────────────────────────────────────────────────────────────────
def find_best_tfidf(X_train, y_train) -> TfidfVectorizer:
    print(f"\n{'=' * 70}")
    print("  STEP 3 — TF-IDF parameter search")
    print("=" * 70)

    configs = [
        {"max_features": 10000, "ngram_range": (1, 1)},
        {"max_features": 10000, "ngram_range": (1, 2)},
        {"max_features": 20000, "ngram_range": (1, 2)},
        {"max_features": 30000, "ngram_range": (1, 2)},
        {"max_features": 50000, "ngram_range": (1, 2)},
    ]

    # Use a fast classifier for TF-IDF comparison
    best_f1 = -1
    best_config = None
    best_vec = None

    for cfg in configs:
        vec = TfidfVectorizer(**cfg, sublinear_tf=True)
        X_vec = vec.fit_transform(X_train)

        clf = LogisticRegression(
            random_state=RANDOM_STATE, max_iter=1000,
            class_weight="balanced", solver="lbfgs"
        )

        # Quick 3-fold CV
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
        scores = []
        for train_idx, val_idx in cv.split(X_vec, y_train):
            clf.fit(X_vec[train_idx], y_train[train_idx])
            y_pred = clf.predict(X_vec[val_idx])
            scores.append(f1_score(y_train[val_idx], y_pred, average="macro"))

        mean_f1 = np.mean(scores)
        print(f"  max_features={cfg['max_features']:>5}, ngram={cfg['ngram_range']} → F1={mean_f1:.4f}")

        if mean_f1 > best_f1:
            best_f1 = mean_f1
            best_config = cfg
            best_vec = vec

    print(f"\n  ✓ Best TF-IDF: max_features={best_config['max_features']}, ngram={best_config['ngram_range']} (F1={best_f1:.4f})")
    return best_vec


# ──────────────────────────────────────────────────────────────────────────────
# STEP 4 — Train all models with hyperparameter tuning
# ──────────────────────────────────────────────────────────────────────────────
def train_and_tune(X_train, X_test, y_train, y_test, vectorizer: TfidfVectorizer):
    print(f"\n{'=' * 70}")
    print("  STEP 4 — Training models with hyperparameter tuning")
    print("=" * 70)

    # Transform data
    X_train_vec = vectorizer.transform(X_train)
    X_test_vec  = vectorizer.transform(X_test)

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)

    # ── Model configs ─────────────────────────────────────────────────────
    model_configs = {
        "Naive Bayes": {
            "model": MultinomialNB(),
            "params": {"alpha": [0.1, 0.5, 1.0, 2.0]},
        },
        "Logistic Regression": {
            "model": LogisticRegression(
                random_state=RANDOM_STATE, max_iter=1000,
                class_weight="balanced", solver="lbfgs",
            ),
            "params": {"C": [0.1, 1.0, 5.0, 10.0]},
        },
        "LinearSVC": {
            "model": LinearSVC(
                random_state=RANDOM_STATE, max_iter=2000,
                class_weight="balanced",
            ),
            "params": {"C": [0.1, 1.0, 5.0, 10.0]},
        },
        "Random Forest": {
            "model": RandomForestClassifier(
                random_state=RANDOM_STATE, n_jobs=-1,
                class_weight="balanced",
            ),
            "params": {
                "n_estimators": [100, 200, 300],
                "max_depth": [None, 20, 40],
            },
        },
    }

    results = {}
    best_overall_f1 = -1
    best_overall_model = None
    best_overall_name = ""
    best_overall_params = {}

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for name, config in model_configs.items():
        print(f"\n  --- {name} ---")
        t0 = time.time()

        grid = GridSearchCV(
            config["model"],
            config["params"],
            scoring="f1_macro",
            cv=cv,
            n_jobs=-1,
            verbose=0,
        )
        grid.fit(X_train_vec, y_train)

        best_model = grid.best_estimator_
        best_params = grid.best_params_
        cv_f1 = grid.best_score_
        elapsed = time.time() - t0

        # Evaluate on test set
        y_pred = best_model.predict(X_test_vec)
        acc  = accuracy_score(y_test, y_pred)
        f1   = f1_score(y_test, y_pred, average="macro")
        prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
        rec  = recall_score(y_test, y_pred, average="macro", zero_division=0)
        cm   = confusion_matrix(y_test, y_pred, labels=CLASS_LABELS)

        report = classification_report(y_test, y_pred, target_names=CLASS_NAMES, zero_division=0)

        print(f"  Best params: {best_params}")
        print(f"  CV F1: {cv_f1:.4f}  |  Test F1: {f1:.4f}  |  Acc: {acc:.4f}")
        print(f"  Precision: {prec:.4f}  |  Recall: {rec:.4f}")
        print(f"  Time: {elapsed:.1f}s")
        print(report)

        # Save as full Pipeline
        pipeline = Pipeline([("tfidf", vectorizer), ("clf", best_model)])
        sane_name = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        model_file = MODELS_DIR / f"{sane_name}.pkl"
        joblib.dump(pipeline, model_file)
        print(f"  Saved → {model_file.name}")

        metrics = {
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "cv_f1": float(cv_f1),
            "best_params": best_params,
            "confusion_matrix": cm.tolist(),
            "training_time_sec": float(elapsed),
        }
        results[name] = metrics

        if f1 > best_overall_f1:
            best_overall_f1 = f1
            best_overall_model = pipeline
            best_overall_name = name
            best_overall_params = best_params

    return results, best_overall_model, best_overall_name, best_overall_params


# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 — Error analysis
# ──────────────────────────────────────────────────────────────────────────────
def error_analysis(model_pipeline, X_test, y_test, n_examples=20):
    print(f"\n{'=' * 70}")
    print(f"  STEP 5 — Error Analysis (top {n_examples} misclassifications)")
    print("=" * 70)

    y_pred = model_pipeline.predict(X_test)

    misclassified = []
    for i, (true, pred) in enumerate(zip(y_test, y_pred)):
        if true != pred:
            misclassified.append({
                "text": X_test[i][:120],
                "true": CLASS_NAMES[int(true)],
                "pred": CLASS_NAMES[int(pred)],
            })

    total_errors = len(misclassified)
    print(f"\n  Total misclassified: {total_errors:,} / {len(y_test):,} ({total_errors/len(y_test)*100:.1f}%)")

    # Error pattern analysis
    error_patterns = {}
    for m in misclassified:
        key = f"{m['true']} → {m['pred']}"
        error_patterns[key] = error_patterns.get(key, 0) + 1

    print(f"\n  Error patterns:")
    for pattern, count in sorted(error_patterns.items(), key=lambda x: -x[1]):
        print(f"    {pattern:30s}: {count:>5,}")

    print(f"\n  Top {min(n_examples, len(misclassified))} misclassified examples:")
    for i, m in enumerate(misclassified[:n_examples]):
        print(f"    {i+1:2d}. [{m['true']:>8s} → {m['pred']:>8s}] \"{m['text']}\"")

    return misclassified


# ──────────────────────────────────────────────────────────────────────────────
# STEP 6 — Save best model and results
# ──────────────────────────────────────────────────────────────────────────────
def save_results(results, best_pipeline, best_name, best_params):
    print(f"\n{'=' * 70}")
    print("  STEP 6 — Saving final model and results")
    print("=" * 70)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save best model
    best_path = MODELS_DIR / "best_model.pkl"
    joblib.dump(best_pipeline, best_path)
    print(f"  ✓ Best model ({best_name}) → {best_path}")

    # Save vectorizer separately for backward compatibility
    vec = best_pipeline.named_steps["tfidf"]
    joblib.dump(vec, MODELS_DIR / "tfidf_vectorizer.pkl")

    # Save label map
    label_map = {str(k): v for k, v in zip(CLASS_LABELS, CLASS_NAMES)}
    with open(MODELS_DIR / "label_map.json", "w") as f:
        json.dump(label_map, f, indent=2)

    # Save results
    results_path = REPORTS_DIR / "model_results.json"
    # Convert numpy types for JSON serialization
    clean_results = {}
    for name, metrics in results.items():
        clean_metrics = {}
        for k, v in metrics.items():
            if k == "best_params":
                clean_metrics[k] = {pk: (pv if not isinstance(pv, (np.integer, np.floating)) else
                                         int(pv) if isinstance(pv, np.integer) else float(pv))
                                    for pk, pv in v.items()}
            else:
                clean_metrics[k] = v
        clean_results[name] = clean_metrics

    with open(results_path, "w") as f:
        json.dump(clean_results, f, indent=2)
    print(f"  ✓ Results → {results_path}")


# ──────────────────────────────────────────────────────────────────────────────
# STEP 7 — Validation tests
# ──────────────────────────────────────────────────────────────────────────────
def final_validation(model_pipeline):
    print(f"\n{'=' * 70}")
    print("  STEP 7 — Final Validation")
    print("=" * 70)

    test_cases = [
        ("The food is so bad", 0, "Negative"),
        ("This product is terrible", 0, "Negative"),
        ("I hate this service", 0, "Negative"),
        ("The worst experience ever", 0, "Negative"),
        ("This product is amazing", 2, "Positive"),
        ("I love this phone", 2, "Positive"),
        ("The service was excellent", 2, "Positive"),
        ("The food was okay", 1, "Neutral"),
        ("The product is average", 1, "Neutral"),
    ]

    passed = 0
    for text, expected, name in test_cases:
        processed = preprocess_pipeline(text) or text.strip().lower()
        pred = int(model_pipeline.predict([processed])[0])
        ok = pred == expected
        status = "✅" if ok else "❌"
        if ok:
            passed += 1
        print(f"  {status} \"{text}\" → {CLASS_NAMES[pred]:10s} (expected {name})")

    print(f"\n  Validation: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main():
    t_start = time.time()

    # Step 1: Load
    df = load_dataset()

    # Step 2: Preprocess
    df = preprocess_dataset(df)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"].values, df["label"].values,
        test_size=TEST_SIZE, stratify=df["label"],
        random_state=RANDOM_STATE,
    )
    print(f"\n  Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    # Step 3: TF-IDF search
    best_vectorizer = find_best_tfidf(X_train, y_train)

    # Step 4: Train and tune
    results, best_pipeline, best_name, best_params = train_and_tune(
        X_train, X_test, y_train, y_test, best_vectorizer
    )

    # Step 5: Error analysis
    error_analysis(best_pipeline, X_test, y_test, n_examples=20)

    # Step 6: Save
    save_results(results, best_pipeline, best_name, best_params)

    # Step 7: Validation
    final_validation(best_pipeline)

    # ── Summary ───────────────────────────────────────────────────────────
    total_time = time.time() - t_start
    print(f"\n{'=' * 70}")
    print("  FINAL COMPARISON TABLE")
    print("=" * 70)
    print(f"\n  {'Model':<25s} | {'Accuracy':>8s} | {'Precision':>9s} | {'Recall':>6s} | {'F1':>6s} | {'CV F1':>6s}")
    print("  " + "-" * 75)
    for name, m in sorted(results.items(), key=lambda x: -x[1]["f1"]):
        marker = " ★" if name == best_name else ""
        print(f"  {name:<25s} | {m['accuracy']:>8.4f} | {m['precision']:>9.4f} | "
              f"{m['recall']:>6.4f} | {m['f1']:>6.4f} | {m['cv_f1']:>6.4f}{marker}")

    print(f"\n  ★ Best model: {best_name}")
    print(f"  ★ Best params: {best_params}")
    print(f"  ★ Test F1: {results[best_name]['f1']:.4f}")
    print(f"  ★ Test Accuracy: {results[best_name]['accuracy']:.4f}")

    print(f"\n  Confusion Matrix ({best_name}):")
    cm = np.array(results[best_name]["confusion_matrix"])
    print(f"  {'':>12s} {'Neg':>8s} {'Neu':>8s} {'Pos':>8s}")
    for i, row_name in enumerate(CLASS_NAMES):
        print(f"  {row_name:>12s} {cm[i,0]:>8d} {cm[i,1]:>8d} {cm[i,2]:>8d}")

    print(f"\n  Total time: {total_time/60:.1f} minutes")
    print("=" * 70)


if __name__ == "__main__":
    main()
