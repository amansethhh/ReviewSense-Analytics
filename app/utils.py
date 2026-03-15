"""Shared utilities for ReviewSense Analytics Streamlit pages."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import joblib
import streamlit as st
from sklearn.pipeline import Pipeline

# Ensure project root is on sys.path so `src` package is importable.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_CSS_PATH = Path(__file__).resolve().parent / "assets" / "style.css"

# Absolute paths to model artifacts, resolved relative to this file so the
# app works regardless of the working directory when Streamlit is launched.
BASE_DIR = Path(__file__).resolve().parents[1]
_MODEL_PATH = BASE_DIR / "models" / "classical" / "best_model.pkl"
_VECTORIZER_PATH = BASE_DIR / "models" / "classical" / "tfidf_vectorizer.pkl"


def load_css() -> None:
    """Inject the shared glassmorphism CSS into the Streamlit page."""
    if _CSS_PATH.exists():
        css_text = _CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css_text}</style>", unsafe_allow_html=True)


@st.cache_resource
def load_model(model_name: str = "best"):
    """Load and cache a trained model pipeline by name.

    For the default ``"best"`` model the function loads
    ``models/classical/best_model.pkl`` directly using an absolute path
    derived from this file's location, so it works regardless of the
    directory from which Streamlit is launched.

    If the saved artifact is already a :class:`sklearn.pipeline.Pipeline` it
    is returned as-is; otherwise ``tfidf_vectorizer.pkl`` is loaded and a
    Pipeline is assembled automatically.

    Returns ``(model_pipeline, label_map)``.  Raises
    :class:`FileNotFoundError` when the requested artifact does not exist.
    """
    from src.config import LABEL_MAP

    if model_name in {"best", "best_model"}:
        model_path = _MODEL_PATH
    else:
        model_path = BASE_DIR / "models" / "classical" / f"{model_name}.pkl"

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model_artifact = joblib.load(model_path)

    if isinstance(model_artifact, Pipeline):
        model_pipeline = model_artifact
    else:
        if not _VECTORIZER_PATH.exists():
            raise FileNotFoundError(f"Vectorizer file not found: {_VECTORIZER_PATH}")
        vectorizer = joblib.load(_VECTORIZER_PATH)
        model_pipeline = Pipeline([("tfidf", vectorizer), ("clf", model_artifact)])

    return model_pipeline, dict(LABEL_MAP)


def render_metric_card(label: str, value: Any, icon: str = "") -> None:
    """Render a styled metric card using st.metric with optional icon prefix."""
    display_label = f"{icon} {label}".strip() if icon else label
    st.metric(display_label, value)


def render_section_header(title: str, subtitle: str = "") -> None:
    """Render a styled section header with an optional subtitle."""
    st.markdown(f"<h2>{title}</h2>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(
            f"<p style='color:#9e9eb8;margin-top:-0.5rem;'>{subtitle}</p>",
            unsafe_allow_html=True,
        )


def render_sidebar(show_model_selector: bool = True) -> dict:
    """Render the common sidebar and return selected options as a dict."""
    from src.config import DOMAINS, MODEL_NAMES

    with st.sidebar:
        st.markdown(
            "<h2 style='background:linear-gradient(90deg,#00e5ff,#b048ff,#ff2d87,#00e5ff);"
            "background-size:300% auto;-webkit-background-clip:text;"
            "-webkit-text-fill-color:transparent;background-clip:text;"
            "animation:neon-shift 4s linear infinite;font-weight:700;'>"
            "🔍 ReviewSense</h2>",
            unsafe_allow_html=True,
        )
        st.markdown("*AI-Powered Sentiment Intelligence*")
        st.markdown("---")

        st.markdown("**📑 Navigation**")
        st.page_link("app.py", label="🏠 Home")
        st.page_link("pages/01_Live_Prediction.py", label="🎯 Live Prediction")
        st.page_link("pages/02_Bulk_Analysis.py", label="📂 Bulk Analysis")
        st.page_link("pages/03_Model_Dashboard.py", label="📊 Model Dashboard")
        st.page_link("pages/04_Language_Analysis.py", label="🌐 Language Analysis")
        st.markdown("---")

        selected_model = "best"
        if show_model_selector:
            selected_model = st.selectbox(
                "🤖 Model",
                ["best"] + MODEL_NAMES,
                index=0,
                key="sidebar_model",
            )

        confidence_threshold = st.slider(
            "🎚️ Confidence Threshold",
            min_value=0.5,
            max_value=1.0,
            value=0.7,
            step=0.05,
            key="sidebar_confidence",
        )

        domain_filter = st.multiselect(
            "🏷️ Domain Filter",
            options=DOMAINS,
            default=[],
            key="sidebar_domains",
        )

        st.markdown("---")
        st.markdown("**👥 Team — Group 19**")
        st.markdown("• Aman Seth")
        st.markdown("• Anmol Bhatnagar")
        st.markdown("• Arjun Kapoor")
        st.caption("Thapar Institute of Engineering & Technology")

    return {
        "model": selected_model,
        "confidence_threshold": confidence_threshold,
        "domain_filter": domain_filter,
    }


def sentiment_badge_html(label_name: str) -> str:
    """Return an HTML pill badge for the given sentiment label."""
    mapping = {
        "Positive": ("badge-positive", "✅ Positive"),
        "Negative": ("badge-negative", "❌ Negative"),
        "Neutral": ("badge-neutral", "🟡 Neutral"),
    }
    css_class, display = mapping.get(label_name, ("badge-neutral", f"🟡 {label_name}"))
    return f"<span class='{css_class}' style='font-size:1.4rem;padding:0.5rem 1.5rem;'>{display}</span>"
