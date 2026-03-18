"""Unified inference pipeline for ReviewSense Analytics.

Performance-optimized:
- Top-level imports (no per-call overhead)
- Vectorized batch sarcasm (predict_batch instead of per-row)
- Chunked sentiment processing for large datasets
- Preload function for eager model initialization
- Progress callback for UI feedback
"""

from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)

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
    if t.count("?") > len(t) * 0.5:
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
    from src.models.translation import _load_helsinki_model

    s_tok, s_model = _load_sentiment_model()
    i_tok, i_model = _load_irony_model()
    t_tok, t_model = _load_helsinki_model()

    return {
        "sentiment_loaded": s_model is not None,
        "sarcasm_loaded": i_model is not None,
        "translation_loaded": t_model is not None,
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
    logger.info("Language detected: %s (%s)", lang_info["name"], lang_code)

    # Step 2: Translate if not English
    if lang_code not in ("en", "unknown"):
        logger.info("Translating text from %s to English", lang_code)
        translated = translate_to_english(original, src_lang=lang_code)
        was_translated = translated.strip().lower() != original.strip().lower()
    else:
        translated = original
        was_translated = False

    # Step 3: Run sentiment on ENGLISH text only
    analysis_text = translated if was_translated else original
    logging.debug("[ReviewSense] INPUT TO MODEL: %s", analysis_text[:200])

    logger.info("Running sentiment prediction")
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
        logger.info("Running sarcasm detection")
        from src.models.sarcasm_model import predict as sarcasm_predict
        sarcasm_result = sarcasm_predict(analysis_text)

    # Step 5: Aspect analysis (optional)
    aspects = []
    if enable_aspects:
        logger.info("Running aspect-based analysis")
        try:
            from src.models.aspect import analyze_aspects
            aspects = analyze_aspects(analysis_text)
        except Exception as e:
            logger.warning("Aspect analysis error: %s", e)
            aspects = []

    logger.info("Pipeline complete — sentiment: %s (%.1f%%)", label_name, confidence * 100)

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
    logger.info("Starting batch analysis: %d reviews", total)

    def _progress(pct: int, msg: str):
        if progress_callback:
            progress_callback(min(pct, 100), msg)

    # ── Step 1+2: Language detection + translation (5%–25%) ──
    _progress(5, "🌐 Detecting languages...")
    translated_texts = []
    lang_infos = []
    for i, text in enumerate(clean_texts):
        if not text:
            translated_texts.append("")
            lang_infos.append({"code": "unknown", "name": "Unknown", "flag_emoji": "🏳️", "was_translated": False})
            continue

        lang = detect_language(text)
        lang_code = lang["code"]
        lang_name = lang["name"]

        if lang_code not in ("en", "unknown"):
            logger.info("🔄 Review %d/%d — %s detected, translating to English", i + 1, total, lang_name)
            tr = translate_to_english(text, src_lang=lang_code)
            was_tr = tr.strip().lower() != text.strip().lower()
            if was_tr:
                logger.info("✅ Review %d/%d — translated from %s", i + 1, total, lang_name)
        else:
            tr = text
            was_tr = False
            logger.info("🔍 Review %d/%d — %s (no translation needed)", i + 1, total, lang_name)

        translated_texts.append(tr if was_tr else text)
        lang_infos.append({**lang, "was_translated": was_tr, "translated": tr})

        # Sync UI progress every 2 rows — smooth without lag
        if i % 2 == 0:
            pct = 5 + int((i + 1) / total * 20)  # 5%–25%
            flag = lang.get("flag_emoji", "🏳️")
            status = "→ EN" if was_tr else "✓"
            _progress(pct, f"🔍 {i+1}/{total} | {flag} {lang_name} {status}")

    # ── Step 3: Batch sentiment (vectorized, chunked) — 25%–60% ──
    _progress(25, f"⚡ Running sentiment model on {total} reviews...")
    logger.info("Running batch sentiment prediction on %d texts", total)
    logging.debug("[ReviewSense] BATCH: %d texts for sentiment model", total)
    sentiments = sentiment_predict_batch(translated_texts)
    logger.info("Batch sentiment complete")
    _progress(60, "✅ Sentiment analysis complete")

    # ── Step 4: Batch sarcasm (vectorized, chunked) — 60%–80% ──
    sarcasm_results = [None] * total
    if enable_sarcasm:
        _progress(60, f"🎭 Running sarcasm detection on {total} reviews...")
        logger.info("Running batch sarcasm detection on %d texts", total)
        from src.models.sarcasm_model import predict_batch as sarcasm_predict_batch
        sarcasm_results = sarcasm_predict_batch(translated_texts)
        logger.info("Batch sarcasm complete")
        _progress(80, "✅ Sarcasm detection complete")

    # ── Step 5: Per-row aspect analysis (if enabled) — 80%–90% ──
    aspect_lists: list[list] = [[] for _ in range(total)]
    if enable_aspects:
        _progress(80, "🔬 Running aspect analysis...")
        logger.info("Running aspect analysis on %d texts", total)
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
        _progress(90, "✅ Aspect analysis complete")

    # ── Assemble results — 90%–100% ──
    _progress(90, "📊 Assembling results...")
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

        # Log final sentiment for each row (throttled)
        if i % 10 == 0:
            logger.info("📋 Review %d/%d — %s (%.0f%%)", i + 1, total, label_name, confidence * 100)

    _progress(100, "✅ Analysis complete!")
    logger.info("Batch analysis complete: %d reviews processed", total)
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
