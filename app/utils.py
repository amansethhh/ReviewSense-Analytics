"""Shared utilities for ReviewSense Analytics Streamlit pages.

Backward-compatible load_model() and sentiment_badge_html().
Now delegates to transformer model modules.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


@st.cache_resource
def load_model(model_name: str = "best"):
    """Load model — returns (pipeline_placeholder, label_map).

    The transformer model is loaded lazily inside predict_sentiment()
    and cached via @st.cache_resource in the model module.
    This function is kept for backward compatibility.
    """
    from src.config import LABEL_MAP
    return None, dict(LABEL_MAP)


def sentiment_badge_html(label_name: str) -> str:
    """Return sentiment badge as raw HTML string."""
    mapping = {
        "Positive": ("badge-positive", "✅ Positive"),
        "Negative": ("badge-negative", "❌ Negative"),
        "Neutral":  ("badge-neutral",  "◼ Neutral"),
        "Uncertain": ("badge-neutral", "⚠️ Uncertain"),
    }
    css_class, display = mapping.get(label_name, ("badge-neutral", f"◼ {label_name}"))
    return f"<span class='{css_class}' style='font-size:1.3rem;padding:0.5rem 1.5rem;'>{display}</span>"