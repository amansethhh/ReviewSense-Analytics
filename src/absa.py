"""Aspect-based sentiment analysis — backward-compatible wrapper.

Delegates to src.models.aspect which uses spaCy + RoBERTa.

ADD-ON 6: compute_dominant_label() uses polarity scores, not review label mode.
"""

from __future__ import annotations

import pandas as pd


def extract_aspects(text):
    """Extract aspects from text using spaCy."""
    from src.models.aspect import extract_aspects as _extract
    return _extract(text)


def get_aspect_dataframe(text):
    """Analyze aspects with RoBERTa and return DataFrame."""
    from src.models.aspect import get_aspect_dataframe as _get_df
    return _get_df(text)


# ═══════════════════════════════════════════════════════════════
# ADD-ON 6 — ABSA dominant label fix
# ═══════════════════════════════════════════════════════════════

def compute_dominant_label(polarity_scores: list[float]) -> str:
    """Compute dominant sentiment label from aspect-level polarity scores.

    Uses average polarity, NOT mode of review labels.
    Returns string names consistent with LABEL_MAP display values.

    Thresholds:
      polarity > 0.20  → Positive
      polarity < -0.20 → Negative
      otherwise        → Neutral
    """
    if not polarity_scores:
        return "Neutral"
    avg = sum(polarity_scores) / len(polarity_scores)
    if avg > 0.20:
        return "Positive"
    elif avg < -0.20:
        return "Negative"
    else:
        return "Neutral"
