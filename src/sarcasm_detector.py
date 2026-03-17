"""Sarcasm detection — delegates to RoBERTa irony model.

Falls back to rules-based if transformer model is unavailable.
"""

from __future__ import annotations


def detect_sarcasm(text, predicted_label=None, star_rating=None):
    """Detect sarcasm using RoBERTa irony classifier.

    predicted_label and star_rating are kept for backward compatibility
    but are not used by the transformer model.
    """
    text = str(text or "").strip()
    if not text:
        return {
            "is_sarcastic": False,
            "confidence": 0.0,
            "reason": "No text provided.",
            "severity": "low",
        }

    try:
        from src.models.sarcasm_model import predict as irony_predict
        return irony_predict(text)
    except Exception as e:
        print(f"[ReviewSense] Sarcasm model fallback to rules: {e}")
        return _rules_fallback(text, predicted_label, star_rating)


def _rules_fallback(text, predicted_label, star_rating):
    """Simple rules-based fallback if transformer is unavailable."""
    try:
        from textblob import TextBlob
        polarity = TextBlob(text).sentiment.polarity
    except Exception:
        polarity = 0.0

    label = int(predicted_label or 1)
    star = float(star_rating) if star_rating is not None else None

    if polarity > 0.35 and label == 0:
        return {"is_sarcastic": True, "confidence": 0.7, "reason": "Positive wording with negative prediction.", "severity": "medium"}
    if star is not None and star <= 2 and polarity > 0.5:
        return {"is_sarcastic": True, "confidence": 0.75, "reason": "Low stars with positive wording.", "severity": "high"}

    return {"is_sarcastic": False, "confidence": 0.05, "reason": "No sarcasm indicators detected.", "severity": "low"}
