"""Prediction helpers for ReviewSense Analytics."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from textblob import TextBlob

from src.config import LABEL_MAP, MODELS_DIR
from src.preprocess import preprocess_pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLASSICAL_MODELS_PATH = PROJECT_ROOT / MODELS_DIR


def _sanitize_model_name(model_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", model_name.strip().lower(), "").strip("_")


def _resolve_model_path(model_name: str) -> Path:
    if model_name in {"best", "best_model"}:
        return CLASSICAL_MODELS_PATH / "best_model.pkl"

    candidate_names = [
        model_name,
        f"{model_name}.pkl",
        _sanitize_model_name(model_name),
        f"{_sanitize_model_name(model_name)}.pkl",
    ]
    available_paths = {path.name.lower(): path for path in CLASSICAL_MODELS_PATH.glob("*.pkl")}

    for candidate_name in candidate_names:
        candidate_key = candidate_name.lower()
        if candidate_key in available_paths:
            return available_paths[candidate_key]

    raise FileNotFoundError(
        f"Could not find a saved model for '{model_name}' in {CLASSICAL_MODELS_PATH}."
    )


def _build_pipeline_if_needed(model_artifact: Any) -> Pipeline:
    """Wrap a bare classifier with the saved vectorizer if needed."""
    if isinstance(model_artifact, Pipeline):
        return model_artifact

    vectorizer_path = CLASSICAL_MODELS_PATH / "tfidf_vectorizer.pkl"
    if not vectorizer_path.exists():
        raise FileNotFoundError(
            "Model artifact is not a Pipeline and tfidf_vectorizer.pkl was not found."
        )

    vectorizer = joblib.load(vectorizer_path)
    return Pipeline([("tfidf", vectorizer), ("clf", model_artifact)])


def _prepare_text_for_inference(text: str) -> str:
    """Apply the SAME preprocessing used during training.

    This ensures TF-IDF feature alignment between training and inference.
    The improved preprocess_pipeline() now returns cleaned text as fallback
    instead of None, so this should rarely need the final fallback.
    """
    processed = preprocess_pipeline(text)
    if processed:
        return processed

    # Final safety net — should rarely reach here after preprocessing fixes
    return str(text or "").strip().lower()


def _get_model_classes(model_pipeline: Pipeline) -> np.ndarray:
    classes = getattr(model_pipeline, "classes_", None)
    if classes is None and hasattr(model_pipeline, "named_steps"):
        classifier = model_pipeline.named_steps.get("clf")
        classes = getattr(classifier, "classes_", None)

    if classes is None:
        return np.array(sorted(LABEL_MAP.keys()))

    return np.asarray(classes)


def _align_scores_to_labels(scores: np.ndarray, classes: np.ndarray) -> np.ndarray:
    label_order = np.array(sorted(LABEL_MAP.keys()))
    aligned_scores = np.zeros(len(label_order), dtype=float)

    for index, label in enumerate(classes):
        try:
            aligned_index = int(np.where(label_order == int(label))[0][0])
        except (TypeError, ValueError, IndexError):
            continue
        aligned_scores[aligned_index] = float(scores[index])

    return aligned_scores


def _softmax(values: np.ndarray) -> np.ndarray:
    stable_values = values - np.max(values)
    exponentials = np.exp(stable_values)
    total = exponentials.sum()
    if total == 0:
        return np.full_like(exponentials, 1.0 / len(exponentials), dtype=float)
    return exponentials / total


def _coerce_label(value: Any) -> int:
    from src.preprocess import normalize_label
    normalized_value = normalize_label(value)
    if normalized_value is not None:
        return int(normalized_value)
    return int(value)


def _estimate_confidence(model_pipeline: Pipeline, prepared_text: str, predicted_label: int) -> float:
    import math

    classes = _get_model_classes(model_pipeline)
    label_order = np.array(sorted(LABEL_MAP.keys()))
    matching_indices = np.where(label_order == predicted_label)[0]
    if matching_indices.size == 0:
        return 0.5
    label_index = int(matching_indices[0])

    if hasattr(model_pipeline, "predict_proba"):
        probabilities = np.asarray(model_pipeline.predict_proba([prepared_text]))[0]
        aligned_probabilities = _align_scores_to_labels(probabilities, classes)
        return float(aligned_probabilities[label_index])

    if hasattr(model_pipeline, "decision_function"):
        decision_scores = np.asarray(model_pipeline.decision_function([prepared_text]))
        if decision_scores.ndim == 1:
            if len(classes) <= 2:
                positive_probability = 1.0 / (1.0 + math.exp(-float(decision_scores[0])))
                probabilities = np.array([1.0 - positive_probability, positive_probability], dtype=float)
                aligned_probabilities = _align_scores_to_labels(probabilities, classes)
            else:
                aligned_probabilities = _align_scores_to_labels(_softmax(decision_scores), classes)
        else:
            aligned_probabilities = _align_scores_to_labels(_softmax(decision_scores[0]), classes)

        return float(aligned_probabilities[label_index])

    return 0.5


def load_model(model_name="best"):
    """Load model pipeline from models/classical/.

    Returns (Pipeline, label_map_dict).
    """
    model_path = _resolve_model_path(model_name)
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model_artifact = joblib.load(model_path)
    model_pipeline = _build_pipeline_if_needed(model_artifact)
    return model_pipeline, dict(LABEL_MAP)


def predict_sentiment(text, model_pipeline):
    """Preprocess text, predict label and confidence.

    Uses the same preprocess_pipeline() that was used during training
    to ensure TF-IDF feature alignment.
    """
    original_text = str(text or "").strip()
    if not original_text:
        return {
            "label": 1,
            "label_name": LABEL_MAP[1],
            "confidence": 0.0,
            "polarity": 0.0,
            "subjectivity": 0.0,
        }

    prepared_text = _prepare_text_for_inference(original_text)
    if not prepared_text:
        prepared_text = original_text.lower()

    predicted_raw_label = model_pipeline.predict([prepared_text])[0]
    predicted_label = _coerce_label(predicted_raw_label)
    confidence = _estimate_confidence(model_pipeline, prepared_text, predicted_label)
    sentiment = TextBlob(original_text).sentiment

    return {
        "label": predicted_label,
        "label_name": LABEL_MAP.get(predicted_label, str(predicted_label)),
        "confidence": float(np.clip(confidence, 0.0, 1.0)),
        "polarity": float(sentiment.polarity),
        "subjectivity": float(sentiment.subjectivity),
    }
