"""LIME explanation helpers for ReviewSense Analytics.

Optimized for speed: reduced num_samples (100), cached results via
@st.cache_data, transformer-based prediction function.

ADD-ON 4: Feature filter to suppress stopword and low-magnitude LIME artifacts.
"""

from __future__ import annotations

import html
import re
from typing import Callable

import numpy as np
import streamlit as st
from lime.lime_text import LimeTextExplainer

from src.config import LABEL_MAP

CLASS_LABELS = sorted(LABEL_MAP.keys())
CLASS_NAMES = [LABEL_MAP[label] for label in CLASS_LABELS]

# Reduced from default for 10x speed improvement
LIME_NUM_SAMPLES = 100
LIME_NUM_FEATURES = 6

# ═══════════════════════════════════════════════════════════════
# ADD-ON 4 — LIME feature filter constants
# ═══════════════════════════════════════════════════════════════

LIME_STOPWORDS_TO_SUPPRESS = {
    "the", "a", "an", "and", "or", "but", "very", "quite", "just",
    "so", "this", "that", "is", "are", "was", "were", "has", "have",
    "had", "it", "its", "for", "of", "to", "in", "on", "at", "with",
}


def _get_prediction_function() -> Callable[[list[str]], np.ndarray]:
    """Return a prediction function compatible with LIME.

    Uses the RoBERTa transformer model for probability estimates.
    """
    from src.models.sentiment import _load_sentiment_model
    import torch

    tokenizer, model = _load_sentiment_model()

    def predict_fn(texts: list[str]) -> np.ndarray:
        results = []
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            inputs = tokenizer(
                batch,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512,
            )
            with torch.no_grad():
                outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1).numpy()
            results.append(probs)

        return np.vstack(results)

    return predict_fn


def filter_lime_features(features: list[tuple[str, float]],
                          threshold: float = 0.05) -> list[tuple[str, float]]:
    """Remove low-magnitude and stopword LIME features from display output.

    These are below the noise floor and actively mislead users.

    ADD-ON 4: Filters out:
      - Features with |weight| < threshold (noise floor)
      - Stopwords with |weight| < 0.08 (LIME artifacts like "quickly")

    Fallback: always returns at least 3 features (top 3 by |weight|)
    even if filtering removes all others.
    """
    filtered = []
    for word, weight in features:
        if abs(weight) < threshold:
            continue
        if word.lower() in LIME_STOPWORDS_TO_SUPPRESS and abs(weight) < 0.08:
            continue
        filtered.append((word, weight))

    if len(filtered) < 3:
        # Fallback — top 3 by magnitude regardless of threshold
        sorted_all = sorted(features, key=lambda x: abs(x[1]), reverse=True)
        return sorted_all[:3]

    return filtered


@st.cache_data(show_spinner=False, ttl=3600)
def explain_prediction(text, num_features=LIME_NUM_FEATURES):
    """Create a LIME explanation for a text prediction.

    Results are cached for 1 hour — repeat analyses are instant.
    Uses reduced num_samples (100) for ~10x speedup.
    ADD-ON 4: Results are filtered via filter_lime_features() before return.
    """
    source_text = str(text or "").strip()
    if not source_text or len(source_text) < 5:
        return []

    prediction_function = _get_prediction_function()
    probabilities = prediction_function([source_text])[0]
    predicted_index = int(np.argmax(probabilities))

    explainer = LimeTextExplainer(class_names=CLASS_NAMES)
    explanation = explainer.explain_instance(
        source_text,
        prediction_function,
        labels=[predicted_index],
        num_features=num_features,
        num_samples=LIME_NUM_SAMPLES,  # 100 instead of default 5000
    )
    word_weights = explanation.as_list(label=predicted_index)
    sorted_weights = sorted(word_weights, key=lambda item: abs(item[1]), reverse=True)

    # ADD-ON 4: Apply feature filter before returning
    return filter_lime_features(sorted_weights)


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
