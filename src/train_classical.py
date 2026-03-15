"""Train classical sklearn sentiment models for ReviewSense Analytics."""

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
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
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
    "Naive Bayes": Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=MAX_FEATURES, ngram_range=NGRAM_RANGE)),
            ("clf", MultinomialNB()),
        ]
    ),
    "LinearSVC": Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=MAX_FEATURES, ngram_range=NGRAM_RANGE)),
            ("clf", LinearSVC(random_state=RANDOM_STATE, max_iter=2000)),
        ]
    ),
    "Logistic Regression": Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=MAX_FEATURES, ngram_range=NGRAM_RANGE)),
            ("clf", LogisticRegression(random_state=RANDOM_STATE, max_iter=1000, C=1.0)),
        ]
    ),
    "Random Forest": Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=MAX_FEATURES, ngram_range=NGRAM_RANGE)),
            ("clf", RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1)),
        ]
    ),
}


def _load_numpy_array(file_path: Path) -> np.ndarray:
    try:
        return np.load(file_path, allow_pickle=False, mmap_mode="r")
    except (ValueError, TypeError):
        return np.load(file_path, allow_pickle=True)


def load_training_data() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load train and test arrays from the processed data directory."""

    required_files = {
        "X_train": PROCESSED_DIR / "X_train.npy",
        "X_test": PROCESSED_DIR / "X_test.npy",
        "y_train": PROCESSED_DIR / "y_train.npy",
        "y_test": PROCESSED_DIR / "y_test.npy",
    }

    missing_files = [str(path) for path in required_files.values() if not path.exists()]
    if missing_files:
        missing_message = ", ".join(missing_files)
        raise FileNotFoundError(f"Missing processed numpy arrays: {missing_message}")

    X_train = _load_numpy_array(required_files["X_train"])
    X_test = _load_numpy_array(required_files["X_test"])
    y_train = np.asarray(_load_numpy_array(required_files["y_train"]), dtype=np.int64)
    y_test = np.asarray(_load_numpy_array(required_files["y_test"]), dtype=np.int64)

    return X_train, X_test, y_train, y_test


def _sanitize_model_name(model_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", model_name.strip().lower()).strip("_")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def save_confusion_matrix_png(cm: np.ndarray, model_name: str) -> Path:
    """Persist a confusion matrix heatmap as a PNG file."""

    FIGURES_PATH.mkdir(parents=True, exist_ok=True)
    output_path = FIGURES_PATH / f"cm_{_sanitize_model_name(model_name)}.png"

    fig, ax = plt.subplots(figsize=(6.5, 5.5), facecolor="#111111")
    image = ax.imshow(cm, cmap="Blues")
    ax.set_facecolor("#111111")
    ax.set_xticks(range(len(CLASS_NAMES)), CLASS_NAMES)
    ax.set_yticks(range(len(CLASS_NAMES)), CLASS_NAMES)
    ax.set_xlabel("Predicted Label", color="white")
    ax.set_ylabel("True Label", color="white")
    ax.set_title(f"{model_name} Confusion Matrix", color="white")
    ax.tick_params(colors="white")

    for row_index in range(cm.shape[0]):
        for column_index in range(cm.shape[1]):
            cell_value = int(cm[row_index, column_index])
            text_color = "white" if cell_value >= cm.max() / 2 else "#111111"
            ax.text(column_index, row_index, cell_value, ha="center", va="center", color=text_color)

    colorbar = fig.colorbar(image, ax=ax)
    colorbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(plt.getp(colorbar.ax.axes, "yticklabels"), color="white")

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

    return output_path


def evaluate_model(model_name: str, model: Pipeline, X_test: np.ndarray, y_test: np.ndarray) -> dict[str, Any]:
    """Evaluate a trained pipeline and collect metrics."""

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    report_text = classification_report(
        y_test,
        y_pred,
        labels=CLASS_LABELS,
        target_names=CLASS_NAMES,
        zero_division=0,
    )
    report_dict = classification_report(
        y_test,
        y_pred,
        labels=CLASS_LABELS,
        target_names=CLASS_NAMES,
        zero_division=0,
        output_dict=True,
    )
    cm = confusion_matrix(y_test, y_pred, labels=CLASS_LABELS)

    print(f"\n{'=' * 80}")
    print(f"Model: {model_name}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")
    print("Classification Report:")
    print(report_text)

    cm_path = save_confusion_matrix_png(cm, model_name)
    print(f"Confusion matrix saved to: {cm_path}")

    return {
        "accuracy": float(accuracy),
        "f1": float(macro_f1),
        "report_dict": _json_safe(report_dict),
        "cm": cm.tolist(),
        "confusion_matrix_path": str(cm_path),
    }


def save_training_artifacts(best_model: Pipeline, results: dict[str, Any]) -> None:
    """Persist the best model, vectorizer, and full training results."""

    MODELS_PATH.mkdir(parents=True, exist_ok=True)
    REPORTS_PATH.mkdir(parents=True, exist_ok=True)

    best_model_path = MODELS_PATH / "best_model.pkl"
    vectorizer_path = MODELS_PATH / "tfidf_vectorizer.pkl"
    results_path = REPORTS_PATH / "model_results.json"

    joblib.dump(best_model, best_model_path)
    joblib.dump(best_model.named_steps["tfidf"], vectorizer_path)

    with results_path.open("w", encoding="utf-8") as json_file:
        json.dump(_json_safe(results), json_file, indent=2)

    print(f"\nBest model saved to: {best_model_path}")
    print(f"TF-IDF vectorizer saved to: {vectorizer_path}")
    print(f"Model results saved to: {results_path}")


def print_comparison_table(results: dict[str, dict[str, Any]]) -> None:
    """Print the final model comparison table."""

    print("\nFinal Comparison Table")
    print("Model | Accuracy | F1 | Training Time")

    comparison_df = pd.DataFrame(
        [
            {
                "Model": model_name,
                "Accuracy": float(metrics["accuracy"]),
                "F1": float(metrics["f1"]),
                "Training Time": float(metrics["training_time_sec"]),
            }
            for model_name, metrics in results.items()
        ]
    ).sort_values(by="F1", ascending=False)

    for model_name, accuracy, f1_score_value, training_time in comparison_df.itertuples(index=False, name=None):
        print(f"{model_name} | {accuracy:.4f} | {f1_score_value:.4f} | {training_time:.2f}s")


def train_all_models() -> dict[str, dict[str, Any]]:
    """Train, evaluate, and persist all configured classical models."""

    MODELS_PATH.mkdir(parents=True, exist_ok=True)
    FIGURES_PATH.mkdir(parents=True, exist_ok=True)

    X_train, X_test, y_train, y_test = load_training_data()
    results: dict[str, dict[str, Any]] = {}
    best_model_name = ""
    best_model_pipeline: Pipeline | None = None
    best_f1 = float("-inf")

    print(f"Loaded X_train: {X_train.shape}, y_train: {y_train.shape}")
    print(f"Loaded X_test: {X_test.shape}, y_test: {y_test.shape}")

    for model_name, model in MODELS.items():
        start_time = time.perf_counter()
        model.fit(X_train, y_train)
        training_time = time.perf_counter() - start_time

        metrics = evaluate_model(model_name, model, X_test, y_test)
        metrics["training_time_sec"] = float(training_time)
        results[model_name] = metrics

        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            best_model_name = model_name
            best_model_pipeline = model

    if best_model_pipeline is None:
        raise RuntimeError("No models were trained successfully.")

    results["best_model"] = {
        "name": best_model_name,
        "f1": float(best_f1),
    }

    save_training_artifacts(best_model_pipeline, results)
    print_comparison_table({name: metrics for name, metrics in results.items() if name in MODELS})

    return results


if __name__ == "__main__":
    train_all_models()
