"""Aspect-based sentiment analysis — backward-compatible wrapper.

Delegates to src.models.aspect which uses spaCy + RoBERTa.
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
