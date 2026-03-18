"""Translation module — Helsinki-NLP/opus-mt-mul-en with googletrans fallback.

Uses HuggingFace MarianMT for offline-capable translation.
Falls back to googletrans if Helsinki model fails to load.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import streamlit as st


@st.cache_resource
def _load_helsinki_model():
    """Load Helsinki-NLP/opus-mt-mul-en for multilingual→English translation."""
    try:
        from transformers import MarianMTModel, MarianTokenizer

        model_id = "Helsinki-NLP/opus-mt-mul-en"
        tokenizer = MarianTokenizer.from_pretrained(model_id)
        model = MarianMTModel.from_pretrained(model_id)
        model.eval()
        return tokenizer, model
    except Exception as e:
        logging.debug("[ReviewSense] Helsinki-NLP model load failed: %s", e)
        return None, None


@lru_cache(maxsize=1)
def _get_googletrans():
    """Fallback translator using googletrans."""
    try:
        from googletrans import Translator
        return Translator()
    except Exception:
        return None


def translate_to_english(text: str, src_lang: str = "auto") -> str:
    """Translate non-English text to English.

    Tries Helsinki-NLP first (offline-capable), falls back to googletrans.
    Returns original text if translation fails.
    """
    text = str(text or "").strip()
    if not text:
        return ""

    # Try Helsinki-NLP MarianMT
    tokenizer, model = _load_helsinki_model()
    if tokenizer is not None and model is not None:
        try:
            import torch

            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                translated_ids = model.generate(**inputs, max_length=512)
            translated = tokenizer.decode(translated_ids[0], skip_special_tokens=True)
            if translated and translated.strip() != text.strip():
                logging.debug("[ReviewSense] Helsinki translated: '%s...' → '%s...'", text[:50], translated[:50])
                return translated.strip()
        except Exception as e:
            logging.debug("[ReviewSense] Helsinki translation error: %s", e)

    # Fallback to googletrans
    translator = _get_googletrans()
    if translator is not None:
        try:
            result = translator.translate(text, src=src_lang if src_lang != "auto" else "auto", dest="en")
            if result and result.text:
                logging.debug("[ReviewSense] Googletrans translated: '%s...' → '%s...'", text[:50], result.text[:50])
                return result.text.strip()
        except Exception as e:
            logging.debug("[ReviewSense] Googletrans translation error: %s", e)

    logging.debug("[ReviewSense] Translation failed, returning original text")
    return text
