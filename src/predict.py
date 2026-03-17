"""Prediction helpers for ReviewSense Analytics.

Now delegates to HuggingFace RoBERTa sentiment model via the pipeline.
Keeps backward-compatible return format for all page callers.
"""

from __future__ import annotations

from src.config import LABEL_MAP


def predict_sentiment(text, model_pipeline=None):
    """Predict sentiment using RoBERTa transformer model.

    The model_pipeline argument is kept for backward compatibility
    but is ignored — the transformer model is used instead.

    Returns dict with: label, label_name, confidence, polarity, subjectivity.
    """
    from src.models.sentiment import predict as transformer_predict
    from src.models.language import detect_language
    from src.models.translation import translate_to_english

    original_text = str(text or "").strip()
    if not original_text:
        return {
            "label": 1,
            "label_name": "Neutral",
            "confidence": 0.0,
            "polarity": 0.0,
            "subjectivity": 0.0,
        }

    # Detect language and translate if needed
    lang = detect_language(original_text)
    if lang["code"] not in ("en", "unknown"):
        analysis_text = translate_to_english(original_text, src_lang=lang["code"])
    else:
        analysis_text = original_text

    print(f"[ReviewSense] INPUT TO MODEL: {analysis_text[:200]}")

    result = transformer_predict(analysis_text)

    scores = result["scores"]  # [neg, neu, pos]
    polarity = scores[2] - scores[0]
    subjectivity = 1.0 - scores[1]

    label_name = result["label_name"]
    confidence = result["confidence"]

    return {
        "label": result["label"],
        "label_name": label_name,
        "confidence": float(confidence),
        "polarity": round(float(polarity), 4),
        "subjectivity": round(float(subjectivity), 4),
    }


def load_model(model_name="best"):
    """Backward-compatible model loader.

    Returns (None, label_map) — the transformer model is loaded
    internally by predict_sentiment() and cached via @st.cache_resource.
    """
    return None, dict(LABEL_MAP)
