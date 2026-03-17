"""Sentiment model — cardiffnlp/twitter-roberta-base-sentiment-latest.

Uses HuggingFace transformers with real softmax probabilities.
Cached via @st.cache_resource so the model loads only once.
"""

from __future__ import annotations

import numpy as np
import streamlit as st
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

MODEL_ID = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# Cardiff RoBERTa label mapping: 0=negative, 1=neutral, 2=positive
ROBERTA_LABEL_MAP = {0: "Negative", 1: "Neutral", 2: "Positive"}


@st.cache_resource
def _load_sentiment_model():
    """Load and cache the RoBERTa sentiment model + tokenizer."""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
    model.eval()
    return tokenizer, model


def predict(text: str) -> dict:
    """Run sentiment prediction on a single English text.

    Returns dict with: label (int), label_name (str), confidence (float),
    scores (list of 3 floats for neg/neu/pos).
    """
    text = str(text or "").strip()
    if not text:
        return {
            "label": 1,
            "label_name": "Neutral",
            "confidence": 0.0,
            "scores": [0.0, 1.0, 0.0],
        }

    tokenizer, model = _load_sentiment_model()
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits[0]
    probs = torch.softmax(logits, dim=0).numpy()
    pred_label = int(np.argmax(probs))
    confidence = float(probs[pred_label])

    return {
        "label": pred_label,
        "label_name": ROBERTA_LABEL_MAP[pred_label],
        "confidence": confidence,
        "scores": [float(p) for p in probs],
    }


def predict_batch(texts: list[str]) -> list[dict]:
    """Batch sentiment prediction for multiple texts.

    Uses padded tokenization for efficient GPU/CPU inference.
    """
    if not texts:
        return []

    tokenizer, model = _load_sentiment_model()

    # Clean inputs
    clean_texts = [str(t or "").strip() or "empty" for t in texts]

    # Batch tokenize
    inputs = tokenizer(
        clean_texts,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512,
    )

    with torch.no_grad():
        outputs = model(**inputs)

    all_probs = torch.softmax(outputs.logits, dim=1).numpy()
    results = []

    for probs in all_probs:
        pred_label = int(np.argmax(probs))
        results.append({
            "label": pred_label,
            "label_name": ROBERTA_LABEL_MAP[pred_label],
            "confidence": float(probs[pred_label]),
            "scores": [float(p) for p in probs],
        })

    return results
