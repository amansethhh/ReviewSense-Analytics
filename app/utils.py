"""Shared utilities for ReviewSense Analytics Streamlit pages.

Backward-compatible load_model() and sentiment_badge_html().
Now includes @st.cache_resource loaders for all models (Problem 7).
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ═══════════════════════════════════════════════════════════════
# Problem 7 — Cached model loaders
# ═══════════════════════════════════════════════════════════════

@st.cache_resource
def load_model(model_name: str = "best"):
    """Load model — returns (pipeline_placeholder, label_map).

    The transformer model is loaded lazily inside predict_sentiment()
    and cached via @st.cache_resource in the model module.
    This function is kept for backward compatibility.
    """
    from src.config import LABEL_MAP
    return None, dict(LABEL_MAP)


@st.cache_resource
def get_roberta_pipeline():
    """Load and cache the RoBERTa sentiment pipeline."""
    from src.models.sentiment import _load_sentiment_model
    return _load_sentiment_model()


@st.cache_resource
def get_lime_explainer():
    """Load and cache the LIME text explainer."""
    from lime.lime_text import LimeTextExplainer
    return LimeTextExplainer(class_names=["Negative", "Neutral", "Positive"])


@st.cache_resource
def get_spacy_model():
    """Load and cache the spaCy model."""
    import spacy
    return spacy.load("en_core_web_sm")


@st.cache_resource
def get_classical_model(model_name: str):
    """Load a classical ML model and its vectorizer."""
    import joblib
    model_path = Path("models/classical") / f"{model_name}.pkl"
    vec_path = Path("models/classical") / "tfidf_vectorizer.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    model = joblib.load(model_path)
    vectorizer = joblib.load(vec_path)
    return model, vectorizer


# ═══════════════════════════════════════════════════════════════
# UI helpers
# ═══════════════════════════════════════════════════════════════

def sentiment_badge_html(label_name: str) -> str:
    """Return sentiment badge as raw HTML string."""
    mapping = {
        "Positive": ("badge-positive", "✅ Positive"),
        "Negative": ("badge-negative", "❌ Negative"),
        "Neutral":  ("badge-neutral",  "◼ Neutral"),
    }
    css_class, display = mapping.get(label_name, ("badge-neutral", f"◼ {label_name}"))
    return f"<span class='{css_class}' style='font-size:1.3rem;padding:0.5rem 1.5rem;'>{display}</span>"