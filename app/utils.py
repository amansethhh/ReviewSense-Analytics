"""Shared utilities for ReviewSense Analytics Streamlit pages.

This module keeps backward-compatible load_model() and sentiment_badge_html()
functions.  The old render_sidebar() and load_css() have moved to ui/sidebar.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import streamlit as st
from sklearn.pipeline import Pipeline

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "models" / "classical"
_VECTOR_PATH = MODELS_DIR / "tfidf_vectorizer.pkl"

# Map UI model names to actual saved filenames
MODEL_FILE_MAP = {
    "best": "best_model.pkl",
    "Naive Bayes": "naive_bayes.pkl",
    "naive_bayes": "naive_bayes.pkl",
    "LinearSVC": "linearsvc.pkl",
    "linearsvc": "linearsvc.pkl",
    "Logistic Regression": "logistic_regression.pkl",
    "logistic_regression": "logistic_regression.pkl",
    "Random Forest": "random_forest.pkl",
    "random_forest": "random_forest.pkl",
}


@st.cache_resource
def load_model(model_name: str = "best"):
    """Load selected model and construct pipeline if needed."""
    from src.config import LABEL_MAP

    if model_name not in MODEL_FILE_MAP:
        raise ValueError(f"Unknown model: {model_name}")

    model_file = MODEL_FILE_MAP[model_name]
    model_path = MODELS_DIR / model_file

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model_artifact = joblib.load(model_path)

    if isinstance(model_artifact, Pipeline):
        model_pipeline = model_artifact
    else:
        if not _VECTOR_PATH.exists():
            raise FileNotFoundError(f"Vectorizer file not found: {_VECTOR_PATH}")
        vectorizer = joblib.load(_VECTOR_PATH)
        model_pipeline = Pipeline([
            ("tfidf", vectorizer),
            ("clf", model_artifact),
        ])

    return model_pipeline, dict(LABEL_MAP)


def sentiment_badge_html(label_name: str) -> str:
    """Return sentiment badge as raw HTML string."""
    mapping = {
        "Positive": ("badge-positive", "✅ Positive"),
        "Negative": ("badge-negative", "❌ Negative"),
        "Neutral":  ("badge-neutral",  "◼ Neutral"),
    }
    css_class, display = mapping.get(label_name, ("badge-neutral", f"◼ {label_name}"))
    return f"<span class='{css_class}' style='font-size:1.3rem;padding:0.5rem 1.5rem;'>{display}</span>"