"""LIME explanation helpers for ReviewSense Analytics."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Callable

import numpy as np
from lime.lime_text import LimeTextExplainer
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.config import LABEL_MAP
from src.preprocess import preprocess_pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CLASS_LABELS = sorted(LABEL_MAP.keys())
CLASS_NAMES = [LABEL_MAP[label] for label in CLASS_LABELS]


def _prepare_text(text: str) -> str:
    """Apply the same preprocessing used during training.

    Uses the improved preprocess_pipeline() that preserves sentiment words
    and falls back to cleaned text instead of returning None.
    """
    processed = preprocess_pipeline(text)
    if processed:
        return processed
    return str(text or "").strip().lower()


def _get_pipeline_classes(model_pipeline: Pipeline) -> np.ndarray:
    classes = getattr(model_pipeline, "classes_", None)
    if classes is None and hasattr(model_pipeline, "named_steps"):
        classifier = model_pipeline.named_steps.get("clf")
        classes = getattr(classifier, "classes_", None)

    if classes is None:
        return np.array(CLASS_LABELS)

    return np.asarray(classes)


def _align_matrix(scores: np.ndarray, classes: np.ndarray) -> np.ndarray:
    scores = np.asarray(scores)
    if scores.ndim == 1:
        scores = scores.reshape(-1, 1)

    if scores.shape[1] == len(CLASS_LABELS) and np.array_equal(np.asarray(classes), np.asarray(CLASS_LABELS)):
        return scores

    aligned_scores = np.zeros((scores.shape[0], len(CLASS_LABELS)), dtype=float)
    label_to_index = {label: index for index, label in enumerate(CLASS_LABELS)}

    if len(classes) == 2 and scores.shape[1] == 1:
        binary_scores = np.column_stack([-scores[:, 0], scores[:, 0]])
        classes = np.asarray(classes)
        scores = binary_scores

    for score_index, class_label in enumerate(classes):
        target_index = label_to_index.get(int(class_label))
        if target_index is not None and score_index < scores.shape[1]:
            aligned_scores[:, target_index] = scores[:, score_index]

    return aligned_scores


def _softmax_rows(scores: np.ndarray) -> np.ndarray:
    stable_scores = scores - np.max(scores, axis=1, keepdims=True)
    exponentials = np.exp(stable_scores)
    totals = exponentials.sum(axis=1, keepdims=True)
    totals[totals == 0] = 1.0
    return exponentials / totals


def _load_validation_data() -> tuple[np.ndarray, np.ndarray]:
    X_val_path = PROCESSED_DIR / "X_val.npy"
    y_val_path = PROCESSED_DIR / "y_val.npy"

    if not X_val_path.exists() or not y_val_path.exists():
        raise FileNotFoundError("Validation arrays X_val.npy and y_val.npy are required for LIME calibration.")

    try:
        X_val = np.load(X_val_path, allow_pickle=False, mmap_mode="r")
    except (ValueError, TypeError):
        X_val = np.load(X_val_path, allow_pickle=True)

    y_val = np.asarray(np.load(y_val_path, allow_pickle=True), dtype=int)
    return X_val, y_val


def _get_prediction_function(model_pipeline: Pipeline) -> Callable[[list[str]], np.ndarray]:
    if hasattr(model_pipeline, "predict_proba"):
        classes = _get_pipeline_classes(model_pipeline)

        def predict_proba(texts: list[str]) -> np.ndarray:
            prepared_texts = [_prepare_text(text) for text in texts]
            probabilities = np.asarray(model_pipeline.predict_proba(prepared_texts))
            return _align_matrix(probabilities, classes)

        return predict_proba

    classifier = model_pipeline.named_steps.get("clf") if hasattr(model_pipeline, "named_steps") else None
    vectorizer = model_pipeline.named_steps.get("tfidf") if hasattr(model_pipeline, "named_steps") else None

    if isinstance(classifier, LinearSVC) and vectorizer is not None:
        calibrator = getattr(model_pipeline, "_lime_calibrator", None)
        if calibrator is None:
            try:
                X_val, y_val = _load_validation_data()
                X_val_transformed = vectorizer.transform(X_val)
                calibrator = CalibratedClassifierCV(estimator=classifier, cv="prefit")
                calibrator.fit(X_val_transformed, y_val)
                setattr(model_pipeline, "_lime_calibrator", calibrator)
            except Exception:
                calibrator = None

        if calibrator is not None:
            calibrated_classes = np.asarray(calibrator.classes_)

            def calibrated_predict_proba(texts: list[str]) -> np.ndarray:
                prepared_texts = [_prepare_text(text) for text in texts]
                transformed_texts = vectorizer.transform(prepared_texts)
                probabilities = np.asarray(calibrator.predict_proba(transformed_texts))
                return _align_matrix(probabilities, calibrated_classes)

            return calibrated_predict_proba

    if hasattr(model_pipeline, "decision_function"):
        classes = _get_pipeline_classes(model_pipeline)

        def decision_predict_proba(texts: list[str]) -> np.ndarray:
            prepared_texts = [_prepare_text(text) for text in texts]
            scores = np.asarray(model_pipeline.decision_function(prepared_texts))
            if scores.ndim == 1:
                scores = scores.reshape(-1, 1)
            aligned_scores = _align_matrix(scores, classes)
            return _softmax_rows(aligned_scores)

        return decision_predict_proba

    raise ValueError("The provided model_pipeline does not support probability-style explanations.")


def explain_prediction(text, model_pipeline, num_features=10):
    """Create a LIME explanation for a text prediction."""

    source_text = str(text or "").strip()
    if not source_text:
        return []

    prediction_function = _get_prediction_function(model_pipeline)
    probabilities = prediction_function([source_text])[0]
    predicted_index = int(np.argmax(probabilities))

    explainer = LimeTextExplainer(class_names=CLASS_NAMES)
    explanation = explainer.explain_instance(
        source_text,
        prediction_function,
        labels=[predicted_index],
        num_features=num_features,
    )
    word_weights = explanation.as_list(label=predicted_index)
    return sorted(word_weights, key=lambda item: abs(item[1]), reverse=True)


def highlight_text_html(text, word_weights):
    """Return HTML with explanation words highlighted by contribution weight."""

    original_text = str(text or "")
    if not original_text:
        return ""

    if not word_weights:
        return f"<div style='line-height:1.8;'>{html.escape(original_text)}</div>"

    weights_by_token = {word.lower(): float(weight) for word, weight in word_weights}
    max_weight = max(abs(weight) for weight in weights_by_token.values()) or 1.0
    tokens = re.findall(r"\w+|\W+", original_text)

    highlighted_tokens = []
    for token in tokens:
        lookup_key = token.lower()
        if lookup_key in weights_by_token and re.match(r"\w+", token):
            weight = weights_by_token[lookup_key]
            intensity = min(1.0, abs(weight) / max_weight)
            alpha = 0.12 + 0.38 * intensity
            background = (
                f"rgba(0,200,81,{alpha:.3f})"
                if weight >= 0
                else f"rgba(255,75,75,{alpha:.3f})"
            )
            highlighted_tokens.append(
                "<span style='background:"
                f"{background};border-radius:3px;padding:2px 4px;'>{html.escape(token)}</span>"
            )
        else:
            highlighted_tokens.append(html.escape(token).replace("\n", "<br>"))

    return f"<div style='line-height:1.8;'>{''.join(highlighted_tokens)}</div>"
