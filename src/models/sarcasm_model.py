"""Sarcasm/irony detection — cardiffnlp/twitter-roberta-base-irony.

Real transformer-based irony detection, replacing rules-based approach.
"""

from __future__ import annotations

import numpy as np
import streamlit as st
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

MODEL_ID = "cardiffnlp/twitter-roberta-base-irony"

# Cardiff irony model: 0=non_irony, 1=irony
IRONY_LABEL_MAP = {0: "non_irony", 1: "irony"}


@st.cache_resource
def _load_irony_model():
    """Load and cache the RoBERTa irony/sarcasm model."""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
    model.eval()
    return tokenizer, model


def predict(text: str) -> dict:
    """Detect sarcasm/irony in English text.

    Returns dict with: is_sarcastic (bool), confidence (float), reason (str).
    """
    text = str(text or "").strip()
    if not text:
        return {
            "is_sarcastic": False,
            "confidence": 0.0,
            "reason": "No text provided.",
        }

    tokenizer, model = _load_irony_model()
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.softmax(outputs.logits[0], dim=0).numpy()
    irony_prob = float(probs[1])
    is_sarcastic = irony_prob > 0.5

    if is_sarcastic:
        reason = f"Irony detected with {irony_prob*100:.1f}% probability by RoBERTa irony classifier."
    else:
        reason = "No sarcasm/irony indicators detected by the model."

    return {
        "is_sarcastic": is_sarcastic,
        "confidence": irony_prob,
        "reason": reason,
        "severity": "high" if irony_prob > 0.8 else "medium" if irony_prob > 0.5 else "low",
    }
