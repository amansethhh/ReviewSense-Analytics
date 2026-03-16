"""Train classical sklearn sentiment models for ReviewSense Analytics.

Each model is saved as a full sklearn Pipeline (TF-IDF + Classifier)
so that inference NEVER needs to reconstruct the pipeline manually.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import label_binarize
from sklearn.svm import LinearSVC

from src.config import MAX_FEATURES, MODELS_DIR, NGRAM_RANGE, RANDOM_STATE, REPORTS_DIR


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_PATH = PROJECT_ROOT / MODELS_DIR
REPORTS_PATH = PROJECT_ROOT / REPORTS_DIR
FIGURES_PATH = REPORTS_PATH / "figures"


CLASS_LABELS = [0, 1, 2]
CLASS_NAMES = ["Negative", "Neutral", "Positive"]


MODELS = {
    "Naive Bayes": MultinomialNB(),
    "LinearSVC": LinearSVC(random_state=RANDOM_STATE, max_iter=2000),
    "Logistic Regression": LogisticRegression(
        random_state=RANDOM_STATE,
        max_iter=1000,
        C=1.0,
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),
}


def _load_numpy_array(file_path: Path) -> np.ndarray:
    try:
        return np.load(file_path, allow_pickle=False, mmap_mode="r")
    except (ValueError, TypeError):
        return np.load(file_path, allow_pickle=True)


def load_training_data():

    required_files = {
        "X_train": PROCESSED_DIR / "X_train.npy",
        "X_test": PROCESSED_DIR / "X_test.npy",
        "y_train": PROCESSED_DIR / "y_train.npy",
        "y_test": PROCESSED_DIR / "y_test.npy",
    }

    for file in required_files.values():
        if not file.exists():
            raise FileNotFoundError(f"Missing file: {file}")

    X_train = _load_numpy_array(required_files["X_train"])
    X_test = _load_numpy_array(required_files["X_test"])
    y_train = _load_numpy_array(required_files["y_train"])
    y_test = _load_numpy_array(required_files["y_test"])

    return X_train, X_test, y_train, y_test


def _sanitize_model_name(name: str):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def save_confusion_matrix_png(cm: np.ndarray, model_name: str):

    FIGURES_PATH.mkdir(parents=True, exist_ok=True)

    output = FIGURES_PATH / f"cm_{_sanitize_model_name(model_name)}.png"

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")

    ax.set_xticks(range(len(CLASS_NAMES)), CLASS_NAMES)
    ax.set_yticks(range(len(CLASS_NAMES)), CLASS_NAMES)

    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(model_name)

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, cm[i, j], ha="center", va="center")

    plt.tight_layout()
    plt.savefig(output, dpi=300)
    plt.close()

    return output


def evaluate_model(model_name, pipeline, X_test, y_test):
    """Evaluate a full Pipeline on raw (preprocessed) test text."""

    y_pred = pipeline.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="macro")
    precision = precision_score(y_test, y_pred, average="macro", zero_division=0)
    recall = recall_score(y_test, y_pred, average="macro", zero_division=0)

    report = classification_report(
        y_test,
        y_pred,
        target_names=CLASS_NAMES,
        zero_division=0
    )

    cm = confusion_matrix(y_test, y_pred, labels=CLASS_LABELS)

    print("\n" + "=" * 80)
    print("Model:", model_name)
    print("Accuracy:", round(acc, 4))
    print("Precision:", round(precision, 4))
    print("Recall:", round(recall, 4))
    print("Macro F1:", round(f1, 4))
    print("Classification Report:")
    print(report)

    cm_path = save_confusion_matrix_png(cm, model_name)

    metrics = {
        "accuracy": float(acc),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "cm_path": str(cm_path),
        "confusion_matrix": cm.tolist(),
    }

    try:
        y_bin = label_binarize(y_test, classes=CLASS_LABELS)

        if hasattr(pipeline, "predict_proba"):
            scores = pipeline.predict_proba(X_test)

        elif hasattr(pipeline, "decision_function"):
            raw = pipeline.decision_function(X_test)
            raw = np.asarray(raw)

            if raw.ndim == 1:
                raw = raw.reshape(-1, 1)

            shifted = raw - raw.max(axis=1, keepdims=True)
            exp_raw = np.exp(shifted)
            scores = exp_raw / exp_raw.sum(axis=1, keepdims=True)

        else:
            scores = None

        if scores is not None:
            fpr, tpr, _ = roc_curve(y_bin.ravel(), scores.ravel())
            roc_auc = float(auc(fpr, tpr))

            metrics["roc"] = {
                "fpr": fpr.tolist(),
                "tpr": tpr.tolist(),
                "auc": roc_auc,
            }

    except Exception:
        pass

    return metrics


def train_all_models():

    X_train, X_test, y_train, y_test = load_training_data()

    print("Loaded X_train:", X_train.shape)
    print("Loaded X_test:", X_test.shape)

    # ── Build TF-IDF vectorizer ──────────────────────────────────────────
    print("\nBuilding TF-IDF features...")

    vectorizer = TfidfVectorizer(
        max_features=MAX_FEATURES,
        ngram_range=NGRAM_RANGE
    )

    # Fit the vectorizer on training data
    vectorizer.fit(X_train)

    results = {}

    best_f1 = -1
    best_pipeline = None
    best_name = ""

    MODELS_PATH.mkdir(parents=True, exist_ok=True)
    REPORTS_PATH.mkdir(parents=True, exist_ok=True)

    for name, model in MODELS.items():

        start = time.time()

        # Create a full Pipeline for each model
        pipeline = Pipeline([
            ("tfidf", vectorizer),
            ("clf", model),
        ])

        # Fit the pipeline (vectorizer is already fitted, clf gets fitted)
        pipeline.fit(X_train, y_train)

        train_time = time.time() - start

        metrics = evaluate_model(name, pipeline, X_test, y_test)

        metrics["training_time_sec"] = train_time

        results[name] = metrics

        # Save the FULL pipeline (vectorizer + classifier together)
        model_file = MODELS_PATH / f"{_sanitize_model_name(name)}.pkl"
        joblib.dump(pipeline, model_file)

        print(f"Saved pipeline → {model_file.name}")

        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            best_pipeline = pipeline
            best_name = name

    # Save the TF-IDF vectorizer separately for backward compatibility
    joblib.dump(vectorizer, MODELS_PATH / "tfidf_vectorizer.pkl")

    # Save best model as a full Pipeline
    joblib.dump(best_pipeline, MODELS_PATH / "best_model.pkl")

    # Save label map
    label_map = {0: "Negative", 1: "Neutral", 2: "Positive"}
    with open(MODELS_PATH / "label_map.json", "w") as f:
        json.dump(label_map, f, indent=2)

    with open(REPORTS_PATH / "model_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nBest model:", best_name)
    print("Saved best_model.pkl (full Pipeline)")

    print("\nFinal Comparison Table")
    print(f"{'Model':<25s} | {'Accuracy':>8s} | {'Precision':>9s} | {'Recall':>6s} | {'F1':>6s} | {'Time':>6s}")
    print("-" * 75)

    df = pd.DataFrame(results).T.sort_values("f1", ascending=False)

    for name, row in df.iterrows():
        print(
            f"{name:<25s} | {row['accuracy']:>8.4f} | {row['precision']:>9.4f} | "
            f"{row['recall']:>6.4f} | {row['f1']:>6.4f} | {row['training_time_sec']:>5.2f}s"
        )


if __name__ == "__main__":
    train_all_models()