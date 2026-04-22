"""Sentiment model — dual model strategy.

English:       cardiffnlp/twitter-roberta-base-sentiment-latest
Multilingual:  cardiffnlp/twitter-xlm-roberta-base-sentiment

The English model is the existing production model.
The XLM model is routed to for non-Latin-script languages (JA, KO, ZH, HI, AR, RU, etc.)
where the English RoBERTa tokenizer produces [UNK] tokens and defaults to NEUTRAL.

Both models share the same label mapping: {0: Negative, 1: Neutral, 2: Positive}.
Cached via double-checked locking so each model loads only once.
"""

from __future__ import annotations

import threading
import logging
import numpy as np
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)
import torch

logger = logging.getLogger("reviewsense.sentiment")

# XLMRobertaTokenizer is needed because AutoTokenizer.from_pretrained
# fails for twitter-xlm-roberta-base-sentiment in transformers>=4.57
# due to a vocab_file NoneType bug in convert_slow_tokenizer.
try:
    from transformers import XLMRobertaTokenizer
    _XLM_TOKENIZER_CLASS = XLMRobertaTokenizer
except ImportError:
    _XLM_TOKENIZER_CLASS = AutoTokenizer

# ═══════════════════════════════════════════════════════════════
# Model IDs
# ═══════════════════════════════════════════════════════════════

ENGLISH_MODEL_ID = "cardiffnlp/twitter-roberta-base-sentiment-latest"
MULTILINGUAL_MODEL_ID = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

# Cardiff RoBERTa label mapping: 0=negative, 1=neutral, 2=positive
ROBERTA_LABEL_MAP = {0: "Negative", 1: "Neutral", 2: "Positive"}

# Backward-compatible name for callers that import it. Routing is stricter
# than this set: English uses RoBERTa; every non-English language uses XLM-R.
XLM_LANGUAGES = frozenset({
    "ar", "bn", "de", "es", "fr", "hi", "it", "ja", "ko",
    "pt", "ru", "zh", "zh-cn", "zh-tw",
})

# ═══════════════════════════════════════════════════════════════
# Model cache (thread-safe, double-checked locking)
# ═══════════════════════════════════════════════════════════════

_MODEL_CACHE: dict = {}
_MODEL_LOCK = threading.Lock()


def _load_model(model_id: str) -> tuple:
    """Load and cache a tokenizer + model pair."""
    if model_id not in _MODEL_CACHE:
        with _MODEL_LOCK:
            if model_id not in _MODEL_CACHE:
                logger.info(f"Loading sentiment model: {model_id}")
                # Use XLMRobertaTokenizer for XLM models
                # (AutoTokenizer crashes on transformers>=4.57)
                if "xlm" in model_id.lower():
                    tokenizer = _XLM_TOKENIZER_CLASS.from_pretrained(model_id)
                else:
                    tokenizer = AutoTokenizer.from_pretrained(model_id)
                model = AutoModelForSequenceClassification.from_pretrained(model_id)
                model.eval()
                if torch.cuda.is_available():
                    model = model.cuda()
                    logger.info(f"  → moved to CUDA")
                _MODEL_CACHE[model_id] = (tokenizer, model)
                logger.info(f"  ✅ {model_id} loaded successfully")
    return _MODEL_CACHE[model_id]


def _load_sentiment_model():
    """Load the English sentiment model (backward-compatible API)."""
    return _load_model(ENGLISH_MODEL_ID)


def _load_multilingual_model():
    """Load the XLM-RoBERTa multilingual model."""
    return _load_model(MULTILINGUAL_MODEL_ID)


def load_all_models():
    """Pre-load both models. Call at application startup."""
    en_pair = _load_model(ENGLISH_MODEL_ID)
    xl_pair = _load_model(MULTILINGUAL_MODEL_ID)
    logger.info("Both sentiment models loaded (EN + XLM)")
    return {"english": en_pair, "multilingual": xl_pair}


def _normalize_lang_code(lang_code: str) -> str:
    """Normalize language codes for hard routing."""
    code = str(lang_code or "en").lower().strip()
    if not code:
        return "en"
    if code in ("english", "eng", "eng_latn"):
        return "en"
    if code.startswith("zh"):
        return "zh"
    return code.split("-")[0][:2]


def _detect_model_for_lang(lang_code: str) -> str:
    """Return the enforced model route for a language code."""
    return "roberta" if _normalize_lang_code(lang_code) == "en" else "xlm-r"


def _model_id_for_language(lang_code: str) -> str:
    """Return the Hugging Face model id for a language code."""
    return (
        ENGLISH_MODEL_ID
        if _detect_model_for_lang(lang_code) == "roberta"
        else MULTILINGUAL_MODEL_ID
    )


def _assert_hard_route(lang_code: str, model_used: str) -> None:
    """Enforce: English -> RoBERTa, non-English -> XLM-R."""
    lang = _normalize_lang_code(lang_code)
    assert (
        (lang == "en" and model_used == "roberta")
        or (lang != "en" and model_used == "xlm-r")
    ), f"Invalid model routing: lang={lang_code!r}, model_used={model_used!r}"


def get_model_for_language(lang_code: str) -> tuple:
    """Route to the correct model based on detected language.

    Returns (tokenizer, model).
    """
    model_used = _detect_model_for_lang(lang_code)
    _assert_hard_route(lang_code, model_used)
    return _load_model(_model_id_for_language(lang_code))


# ═══════════════════════════════════════════════════════════════
# Single prediction
# ═══════════════════════════════════════════════════════════════

def predict(text: str, lang_code: str = "en") -> dict:
    """Run sentiment prediction on a single text.

    Routes to English or XLM model based on language.

    Returns dict with: label (int), label_name (str), confidence (float),
    scores (list of 3 floats for neg/neu/pos).
    """
    text = str(text or "").strip()
    if not text:
        model_used = _detect_model_for_lang(lang_code)
        _assert_hard_route(lang_code, model_used)
        return {
            "label": 1,
            "label_name": "Neutral",
            "confidence": 0.0,
            "scores": [0.0, 1.0, 0.0],
            "model_used": model_used,
        }

    model_used = _detect_model_for_lang(lang_code)
    _assert_hard_route(lang_code, model_used)
    tokenizer, model = get_model_for_language(lang_code)
    device = next(model.parameters()).device

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits[0]
    probs = torch.softmax(logits, dim=0)
    if device.type != "cpu":
        probs = probs.cpu()
    probs = probs.numpy()

    pred_label = int(np.argmax(probs))
    confidence = float(probs[pred_label])

    return {
        "label": pred_label,
        "label_name": ROBERTA_LABEL_MAP[pred_label],
        "confidence": confidence,
        "scores": [float(p) for p in probs],
        "model_used": model_used,
    }


# ═══════════════════════════════════════════════════════════════
# Batch prediction (language-grouped)
# ═══════════════════════════════════════════════════════════════

def predict_batch(
    texts: list[str],
    lang_codes: list[str] | None = None,
    batch_size: int = 32,
) -> list[dict]:
    """Batch sentiment prediction with language-aware model routing.

    Groups texts by model type (EN vs XLM), runs each group
    as batched inference, then merges results in original order.

    Args:
        texts: List of text strings (in original language)
        lang_codes: ISO 639-1 codes per text (None = all English)
        batch_size: Inference batch size per model call

    Returns: List of result dicts in same order as input.
    """
    if not texts:
        return []

    n = len(texts)
    if lang_codes is None:
        lang_codes = ["en"] * n

    # Clean inputs
    clean_texts = [str(t or "").strip() or "empty" for t in texts]
    results = [None] * n

    # Group indices by the hard route: en -> RoBERTa, else XLM-R.
    en_indices = []
    xl_indices = []
    for i, lc in enumerate(lang_codes):
        model_used = _detect_model_for_lang(lc)
        _assert_hard_route(lc, model_used)
        if model_used == "roberta":
            en_indices.append(i)
        else:
            xl_indices.append(i)

    def _run_model_group(indices: list, model_id: str):
        if not indices:
            return
        tokenizer, model = _load_model(model_id)
        device = next(model.parameters()).device

        for batch_start in range(0, len(indices), batch_size):
            batch_indices = indices[batch_start:batch_start + batch_size]
            batch_texts = [clean_texts[i] for i in batch_indices]

            inputs = tokenizer(
                batch_texts,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512,
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = model(**inputs)

            batch_probs = torch.softmax(outputs.logits, dim=1)
            if device.type != "cpu":
                batch_probs = batch_probs.cpu()
            batch_probs = batch_probs.numpy()

            for j, orig_idx in enumerate(batch_indices):
                probs = batch_probs[j]
                pred_label = int(np.argmax(probs))
                results[orig_idx] = {
                    "label": pred_label,
                    "label_name": ROBERTA_LABEL_MAP[pred_label],
                    "confidence": float(probs[pred_label]),
                    "scores": [float(p) for p in probs],
                    "model_used": (
                        "roberta"
                        if model_id == ENGLISH_MODEL_ID
                        else "xlm-r"
                    ),
                }

    # Run English group
    _run_model_group(en_indices, ENGLISH_MODEL_ID)
    # Run multilingual group
    _run_model_group(xl_indices, MULTILINGUAL_MODEL_ID)

    # Safety: fill any None results (should not happen)
    for i in range(n):
        if results[i] is None:
            results[i] = {
                "label": 1,
                "label_name": "Neutral",
                "confidence": 0.0,
                "scores": [0.0, 1.0, 0.0],
                "model_used": _detect_model_for_lang(lang_codes[i]),
            }

    return results
