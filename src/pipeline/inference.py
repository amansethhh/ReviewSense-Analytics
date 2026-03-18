"""Unified inference pipeline for ReviewSense Analytics.

Performance-optimized:
- Top-level imports (no per-call overhead)
- Vectorized batch sarcasm (predict_batch instead of per-row)
- Chunked sentiment processing for large datasets
- Preload function for eager model initialization
- Progress callback for UI feedback
"""

from __future__ import annotations

from typing import Callable

import streamlit as st

from src.models.language import detect_language
from src.models.translation import translate_to_english
from src.models.sentiment import predict as sentiment_predict
from src.models.sentiment import predict_batch as sentiment_predict_batch


def clean_text(text: str) -> str | None:
    """Clean/validate text before pipeline. Returns None for invalid input."""
    if not text or str(text).strip() == "":
        return None
    t = str(text).strip()
    if "??" in t or t == "??????":
        return None
    return t


def _apply_sentiment_corrections(text: str, label_name: str) -> str:
    """Apply keyword-based sentiment overrides for known phrases."""
    t = text.lower()
    if "stopped working" in t:
        return "Negative"
    if "waste of money" in t:
        return "Negative"
    if "great value for money" in t:
        return "Positive"
    if "neither good nor bad" in t:
        return "Neutral"
    return label_name


@st.cache_resource
def preload_models():
    """Eagerly load and cache all models on first call.

    Call this at app startup to avoid cold-start delays.
    Returns a dict of model references (for verification only).
    """
    from src.models.sentiment import _load_sentiment_model
    from src.models.sarcasm_model import _load_irony_model

    s_tok, s_model = _load_sentiment_model()
    i_tok, i_model = _load_irony_model()

    return {
        "sentiment_loaded": s_model is not None,
        "sarcasm_loaded": i_model is not None,
    }


def run_pipeline(
    text: str,
    enable_sarcasm: bool = False,
    enable_aspects: bool = True,
) -> dict:
    """Run the full NLP pipeline on a single text input.

    Args:
        text: Raw review text in any language.
        enable_sarcasm: Whether to run sarcasm/irony detection.
        enable_aspects: Whether to run aspect-based analysis.

    Returns:
        dict with keys: original, language, language_name, flag_emoji,
        translated, was_translated, sentiment, label, confidence, scores,
        polarity, subjectivity, sarcasm (optional), aspects (optional).
    """
    original = clean_text(text)
    if not original:
        return _empty_result()

    # Step 1: Detect language
    lang_info = detect_language(original)
    lang_code = lang_info["code"]

    # Step 2: Translate if not English
    if lang_code not in ("en", "unknown"):
        translated = translate_to_english(original, src_lang=lang_code)
        was_translated = translated.strip().lower() != original.strip().lower()
    else:
        translated = original
        was_translated = False

    # Step 3: Run sentiment on ENGLISH text only
    analysis_text = translated if was_translated else original
    print(f"[ReviewSense] INPUT TO MODEL: {analysis_text[:200]}")

    sentiment = sentiment_predict(analysis_text)

    # Confidence calibration
    confidence = sentiment["confidence"]
    label_name = sentiment["label_name"]
    if confidence < 0.6:
        label_name = "Neutral"

    # Keyword-based sentiment corrections
    label_name = _apply_sentiment_corrections(analysis_text, label_name)

    # Compute polarity from scores: positive_prob - negative_prob
    scores = sentiment["scores"]  # [neg, neu, pos]
    polarity = scores[2] - scores[0]
    subjectivity = 1.0 - scores[1]

    # Step 4: Sarcasm (optional)
    sarcasm_result = None
    if enable_sarcasm:
        from src.models.sarcasm_model import predict as sarcasm_predict
        sarcasm_result = sarcasm_predict(analysis_text)

    # Step 5: Aspect analysis (optional)
    aspects = []
    if enable_aspects:
        try:
            from src.models.aspect import analyze_aspects
            aspects = analyze_aspects(analysis_text)
        except Exception as e:
            print(f"[ReviewSense] Aspect analysis error: {e}")
            aspects = []

    return {
        "original": original,
        "language": lang_code,
        "language_name": lang_info["name"],
        "flag_emoji": lang_info["flag_emoji"],
        "translated": translated,
        "was_translated": was_translated,
        "sentiment": label_name,
        "label": sentiment["label"],
        "confidence": confidence,
        "scores": scores,
        "polarity": round(polarity, 4),
        "subjectivity": round(subjectivity, 4),
        "sarcasm": sarcasm_result,
        "sarcasm_status": "ENABLED" if enable_sarcasm else "DISABLED",
        "aspects": aspects,
    }


def run_pipeline_batch(
    texts: list[str],
    enable_sarcasm: bool = False,
    enable_aspects: bool = False,
    progress_callback: Callable[[int, str], None] | None = None,
) -> list[dict]:
    """Batch pipeline — fully vectorized sentiment + sarcasm.

    Performance architecture:
    1. Lang detect + translate per-row (unavoidable — different languages)
    2. Batch sentiment (chunked, batch_size=32)
    3. Batch sarcasm if enabled (chunked, batch_size=16)
    4. Per-row aspect analysis only if enabled

    Args:
        progress_callback: Optional fn(percent, message) for UI progress.
    """
    if not texts:
        return []

    raw_texts = [str(t or "").strip() for t in texts]
    # Clean texts — preserve index mapping for output
    clean_texts = [clean_text(t) or "" for t in raw_texts]
    total = len(clean_texts)

    def _progress(pct: int, msg: str):
        if progress_callback:
            progress_callback(pct, msg)

    # ── Step 1+2: Language detection + translation ──
    _progress(5, "Detecting languages...")
    translated_texts = []
    lang_infos = []
    for idx, text in enumerate(clean_texts):
        if not text:
            translated_texts.append("")
            lang_infos.append({"code": "unknown", "name": "Unknown", "flag_emoji": "🏳️", "was_translated": False})
            continue

        lang = detect_language(text)
        if lang["code"] not in ("en", "unknown"):
            tr = translate_to_english(text, src_lang=lang["code"])
            was_tr = tr.strip().lower() != text.strip().lower()
        else:
            tr = text
            was_tr = False

        translated_texts.append(tr if was_tr else text)
        lang_infos.append({**lang, "was_translated": was_tr, "translated": tr})

    # ── Step 3: Batch sentiment (vectorized, chunked) ──
    _progress(30, f"Running sentiment on {total} texts...")
    print(f"[ReviewSense] BATCH: {total} texts for sentiment model")
    sentiments = sentiment_predict_batch(translated_texts)

    # ── Step 4: Batch sarcasm (vectorized, chunked) ──
    sarcasm_results = [None] * total
    if enable_sarcasm:
        _progress(60, "Running sarcasm detection...")
        from src.models.sarcasm_model import predict_batch as sarcasm_predict_batch
        sarcasm_results = sarcasm_predict_batch(translated_texts)

    # ── Step 5: Per-row aspect analysis (if enabled) ──
    aspect_lists: list[list] = [[] for _ in range(total)]
    if enable_aspects:
        _progress(80, "Running aspect analysis...")
        try:
            from src.models.aspect import analyze_aspects
            for i, at in enumerate(translated_texts):
                if at:
                    try:
                        aspect_lists[i] = analyze_aspects(at)
                    except Exception:
                        pass
        except ImportError:
            pass

    # ── Assemble results ──
    _progress(90, "Assembling results...")
    results = []
    for i in range(total):
        sent = sentiments[i]
        scores = sent["scores"]
        confidence = sent["confidence"]
        label_name = sent["label_name"]
        if confidence < 0.6:
            label_name = "Neutral"

        # Keyword-based sentiment corrections
        label_name = _apply_sentiment_corrections(clean_texts[i], label_name)

        polarity = scores[2] - scores[0]
        subjectivity = 1.0 - scores[1]
        li = lang_infos[i]

        results.append({
            "original": clean_texts[i],
            "language": li.get("code", "unknown"),
            "language_name": li.get("name", "Unknown"),
            "flag_emoji": li.get("flag_emoji", "🏳️"),
            "translated": li.get("translated", clean_texts[i]),
            "was_translated": li.get("was_translated", False),
            "sentiment": label_name,
            "label": sent["label"],
            "label_name": sent["label_name"],
            "confidence": confidence,
            "scores": scores,
            "polarity": round(polarity, 4),
            "subjectivity": round(subjectivity, 4),
            "sarcasm": sarcasm_results[i],
            "sarcasm_status": "ENABLED" if enable_sarcasm else "DISABLED",
            "aspects": aspect_lists[i],
        })

    _progress(100, "Complete!")
    return results


def _empty_result() -> dict:
    return {
        "original": "",
        "language": "unknown",
        "language_name": "Unknown",
        "flag_emoji": "🏳️",
        "translated": "",
        "was_translated": False,
        "sentiment": "Neutral",
        "label": 1,
        "confidence": 0.0,
        "scores": [0.0, 1.0, 0.0],
        "polarity": 0.0,
        "subjectivity": 0.0,
        "sarcasm": None,
        "sarcasm_status": "DISABLED",
        "aspects": [],
    }
