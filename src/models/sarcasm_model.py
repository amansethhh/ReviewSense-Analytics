"""Sarcasm/irony detection — cardiffnlp/twitter-roberta-base-irony.

Real transformer-based irony detection with batch support.
"""

from __future__ import annotations

import threading
import numpy as np
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

MODEL_ID = "cardiffnlp/twitter-roberta-base-irony"

# Cardiff irony model: 0=non_irony, 1=irony
IRONY_LABEL_MAP = {0: "non_irony", 1: "irony"}


_MODEL_CACHE: dict = {}
_MODEL_LOCK = threading.Lock()


def _load_irony_model():
    """Load and cache the RoBERTa irony/sarcasm model (framework-agnostic)."""
    if "model" not in _MODEL_CACHE:
        with _MODEL_LOCK:
            if "model" not in _MODEL_CACHE:  # double-checked locking
                tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
                model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
                model.eval()
                _MODEL_CACHE["model"] = (tokenizer, model)
    return _MODEL_CACHE["model"]


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
    is_sarcastic = irony_prob > 0.80

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


def predict_batch(texts: list[str], batch_size: int = 16) -> list[dict]:
    """Batch sarcasm/irony detection — vectorized inference.

    Processes texts in chunks of batch_size for memory efficiency.
    """
    if not texts:
        return []

    tokenizer, model = _load_irony_model()
    clean_texts = [str(t or "").strip() or "empty" for t in texts]
    results = []

    for i in range(0, len(clean_texts), batch_size):
        batch = clean_texts[i:i + batch_size]
        inputs = tokenizer(
            batch,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512,
        )

        with torch.no_grad():
            outputs = model(**inputs)

        all_probs = torch.softmax(outputs.logits, dim=1).numpy()

        for probs in all_probs:
            irony_prob = float(probs[1])
            is_sarcastic = irony_prob > 0.80
            results.append({
                "is_sarcastic": is_sarcastic,
                "confidence": irony_prob,
                "reason": f"Irony detected with {irony_prob*100:.1f}% probability." if is_sarcastic else "No sarcasm detected.",
                "severity": "high" if irony_prob > 0.8 else "medium" if irony_prob > 0.5 else "low",
            })

    return results
