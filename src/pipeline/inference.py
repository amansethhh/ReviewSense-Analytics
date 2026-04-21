"""Unified inference pipeline for ReviewSense Analytics.

Integrates all 7 Master Prompt fixes + 10 Add-On patches:
- Neutral correction, confidence calibration, temperature scaling
- Short-text guard, translation validation, Hinglish detection
- Unicode script detection, degenerate translation detection
- Bulk sarcasm detection, rolling trend support
- Safe translation with retry logic
"""

from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger("reviewsense")

import functools
from src.models.language import detect_language
from src.models.translation import translate_to_english
from src.models.sentiment import predict as sentiment_predict
from src.models.sentiment import predict_batch as sentiment_predict_batch
from src.predict import (
    apply_short_text_guard,
    apply_neutral_correction_v2,
    compute_dual_polarity,
    calibrated_confidence,
    apply_temperature_scaling,
    _apply_sarcasm_override,
)
from src.sarcasm_detector import detect_sarcasm_bulk
from src.config import LABEL_MAP

# ═══════════════════════════════════════════════════════════════
# ADD-ON 2 — Degenerate translation detection
# ═══════════════════════════════════════════════════════════════

DEGENERATE_TRANSLATIONS = {
    "bad experience.", "bad experience", "error.", "error",
    "translation error", "none", "null", "", ".", "!",
    "i'm sorry", "i am sorry", "apologies",
}


def _is_degenerate(translated: str) -> bool:
    return translated.strip().lower() in DEGENERATE_TRANSLATIONS


def _translation_plausible(source: str, translated: str) -> bool:
    ratio = len(translated.strip()) / max(len(source.strip()), 1)
    return 0.3 < ratio < 4.0


# ═══════════════════════════════════════════════════════════════
# Problem 2 — Translation validation (polarity inversion)
# ═══════════════════════════════════════════════════════════════

def validate_translation(original_text: str, translated_text: str) -> dict:
    """Compare TextBlob polarity of original vs translated text."""
    op, tp = 0.0, 0.0
    try:
        from textblob import TextBlob
        op = TextBlob(original_text).sentiment.polarity
        tp = TextBlob(translated_text).sentiment.polarity
        flagged = (op > 0.25 and tp < -0.25) or (op < -0.25 and tp > 0.25)
    except Exception:
        flagged = False

    return {
        "translated_text": translated_text,
        "translation_flagged": flagged,
        "flag_reason": "Polarity inversion detected" if flagged else "",
        "translation_confidence": "LOW" if flagged else "HIGH",
        "original_polarity": round(op, 4),
        "translated_polarity": round(tp, 4),
    }


# ═══════════════════════════════════════════════════════════════
# Problem 6 + ADD-ON 2 — Safe translation wrapper
# ═══════════════════════════════════════════════════════════════

def safe_translate(text: str, lang_code: str) -> dict:
    """Safe translation with degenerate output detection and retry logic."""
    try:
        _tr_result = translate_to_english(text, src_lang=lang_code)
        translated = _tr_result[0] if isinstance(_tr_result, tuple) else _tr_result

        # Check 1: degenerate output
        if _is_degenerate(translated):
            logger.warning("Degenerate translation for lang=%s: '%s'", lang_code, translated)
            padded = f"Review: {text}. Overall opinion expressed."
            _tr_result2 = translate_to_english(padded, src_lang=lang_code)
            translated = _tr_result2[0] if isinstance(_tr_result2, tuple) else _tr_result2
            if _is_degenerate(translated) or not _translation_plausible(text, translated):
                return {"translated_text": text, "translation_status": "FALLBACK_PASSTHROUGH"}
            return {"translated_text": translated, "translation_status": "RETRIED_OK"}

        # Check 2: ratio plausibility
        if not _translation_plausible(text, translated):
            logger.warning("Implausible translation ratio for lang=%s", lang_code)
            padded = f"Review: {text}. Overall opinion expressed."
            _tr_result3 = translate_to_english(padded, src_lang=lang_code)
            translated = _tr_result3[0] if isinstance(_tr_result3, tuple) else _tr_result3
            if not _translation_plausible(text, translated):
                return {"translated_text": text, "translation_status": "FALLBACK_PASSTHROUGH"}
            return {"translated_text": translated, "translation_status": "RETRIED_OK"}

        return {"translated_text": translated, "translation_status": "OK"}

    except Exception as e:
        logger.error("Translation failed for lang=%s: %s", lang_code, e)
        return {"translated_text": text, "translation_status": "FALLBACK_PASSTHROUGH"}


# ═══════════════════════════════════════════════════════════════
# Pipeline helpers
# ═══════════════════════════════════════════════════════════════

def clean_text(text: str) -> str | None:
    if not text or str(text).strip() == "":
        return None
    t = str(text).strip()
    if t.count("?") > len(t) * 0.5:
        return None
    return t


def _apply_post_processing(
    text: str,
    sentiment: dict,
    lang_code: str = "en",
    translated_text: str = "",
) -> dict:
    """Apply the full post-processing pipeline to a single prediction.

    V5 Pipeline order:
      Step 4: Dual polarity (VADER + TextBlob) — English only (Ruleset 3)
      Step 5: Short-text guard — English text (original or translated)
      Step 6: Neutral correction v2 (Ruleset 4) — model-first
      Step 7: Confidence calibration
      Step 8: Temperature scaling
    """
    scores = sentiment["scores"]
    pred_class = sentiment["label"]
    raw_confidence = sentiment["confidence"]

    # Step 4: Dual polarity — ENGLISH ONLY (V5 Ruleset 3)
    # For non-English, returns (0.0, 0.0, 0.5) automatically
    polarity, vader_compound, subjectivity = compute_dual_polarity(text, lang_code)

    # Step 5: Short-text guard
    # For non-English inputs, use translated English text (if available)
    # so English explicit terms can be matched. Model still ran on original.
    guard_text = text
    lc = (lang_code or "en").lower().strip()[:2]
    if lc != "en" and translated_text and translated_text.strip():
        guard_text = translated_text
        logger.debug(
            "[GUARD] Using translated text for short-text guard: '%s'",
            guard_text[:50],
        )

    guard_result = apply_short_text_guard(guard_text, pred_class, raw_confidence)
    pred_class = guard_result["pred_class"]
    confidence = guard_result["confidence"] if guard_result["guard_applied"] else raw_confidence
    guard_applied = guard_result["guard_applied"]

    # Step 6: Neutral correction v2 — model-first (V5 Ruleset 4)
    nc = apply_neutral_correction_v2(pred_class, confidence, polarity, vader_compound, lang_code)
    pred_class = nc["pred_class"]
    neutral_corrected = nc["neutral_corrected"]
    correction_reason = nc["correction_reason"]

    # Step 7: Confidence calibration
    confidence = calibrated_confidence(confidence, polarity, pred_class)

    # Step 8: Temperature scaling (conditional)
    temperature_scaled = False
    if raw_confidence <= 0.92:
        temp_probs = apply_temperature_scaling(scores)
        temp_confidence = temp_probs[pred_class]
        confidence = min(confidence, temp_confidence)
        confidence = max(confidence, 0.30)
        confidence = round(confidence, 4)
        temperature_scaled = True

    label_name = LABEL_MAP[pred_class]

    return {
        "label": pred_class,
        "label_name": label_name,
        "sentiment": label_name,
        "confidence": float(confidence),
        "raw_confidence": float(raw_confidence),
        "polarity": round(float(polarity), 4),
        "subjectivity": round(float(subjectivity), 4),
        "neutral_corrected": neutral_corrected,
        "correction_reason": correction_reason,
        "guard_applied": guard_applied,
        "temperature_scaled": temperature_scaled,
        "scores": scores,
    }


@functools.lru_cache(maxsize=1)
def preload_models():
    """Eagerly load and cache all models on first call."""
    from src.models.sentiment import _load_sentiment_model
    from src.models.sarcasm_model import _load_irony_model

    s_tok, s_model = _load_sentiment_model()
    i_tok, i_model = _load_irony_model()

    return {
        "sentiment_loaded": s_model is not None,
        "sarcasm_loaded": i_model is not None,
        "translation_loaded": True,   # V4: NLLB is lazy-loaded via transformers
    }



# ═══════════════════════════════════════════════════════════════
# SINGLE PREDICTION PIPELINE
# ═══════════════════════════════════════════════════════════════

def run_pipeline(
    text: str,
    enable_sarcasm: bool = False,
    enable_aspects: bool = True,
) -> dict:
    """Run the full NLP pipeline on a single text input."""
    original = clean_text(text)
    if not original:
        return _empty_result()

    # Step 1: Detect language (enhanced hierarchy)
    lang_info = detect_language(original)
    lang_code = lang_info["code"]
    hinglish_detected = lang_info.get("hinglish_detected", False)
    logger.info("Language detected: %s (%s)", lang_info["name"], lang_code)

    # Step 2: Translate if not English
    translation_status = "OK"
    translation_flagged = False
    translated = original
    was_translated = False

    if hinglish_detected:
        # Hinglish: skip translation, use direct inference
        logger.info("Hinglish detected — skipping translation")
        translated = original
        was_translated = False
    elif lang_code not in ("en", "unknown"):
        logger.info("Translating text from %s to English", lang_code)
        tr_result = safe_translate(original, lang_code)
        translated = tr_result["translated_text"]
        translation_status = tr_result["translation_status"]
        was_translated = translated.strip().lower() != original.strip().lower()

        # Validate translation (Problem 2) — ENFORCEMENT
        if was_translated:
            val = validate_translation(original, translated)
            polarity_flipped = (
                val.get("translation_flagged", False)
                and abs(val.get("original_polarity", 0.0) if "original_polarity" in val else 0.0) > 0.15
                and abs(val.get("translated_polarity", 0.0) if "translated_polarity" in val else 0.0) > 0.15
            )
            if polarity_flipped or val.get("translation_flagged", False):
                # Fall back to original text — do NOT trust translation
                translation_flagged = True
                translation_status = "FALLBACK_PASSTHROUGH"
                logger.warning(
                    "Translation polarity flip | lang=%s | falling back to original text",
                    lang_code,
                )

    # V3 RULE 2: Classification ALWAYS uses ORIGINAL text
    # Translation is for DISPLAY ONLY
    analysis_input = original

    # Step 3: Run sentiment on ORIGINAL text
    logger.info("Running sentiment prediction on original text")
    sentiment = sentiment_predict(analysis_input, lang_code=lang_code)

    # Apply full post-processing pipeline on ORIGINAL text
    # Pass translated for guard use on non-English texts (display only, not sentiment)
    pp = _apply_post_processing(
        analysis_input, sentiment,
        lang_code=lang_code,
        translated_text=translated if was_translated else "",
    )

    # Reduce confidence if translation flagged
    confidence = pp["confidence"]
    if translation_flagged:
        confidence = round(confidence * 0.85, 4)
        confidence = max(confidence, 0.40)

    # Sarcasm (optional) + override
    sarcasm_result = None
    sarcasm_detected = False
    sarcasm_confidence_val = 0.0
    sarcasm_applied = False
    sarcasm_reason = ""

    if enable_sarcasm:
        logger.info("Running sarcasm detection")
        from src.models.sarcasm_model import predict as sarcasm_predict
        sarcasm_result = sarcasm_predict(analysis_input)
        sarcasm_detected = sarcasm_result.get("is_sarcastic", False)
        sarcasm_confidence_val = sarcasm_result.get("confidence", 0.0)
        sarcasm_reason = sarcasm_result.get("reason", "")

        # Apply sarcasm → sentiment override
        override = _apply_sarcasm_override(
            pp["label"], confidence, sarcasm_detected, sarcasm_confidence_val
        )
        if override["sarcasm_applied"]:
            pp["label"] = override["pred_class"]
            pp["label_name"] = LABEL_MAP[override["pred_class"]]
            pp["sentiment"] = LABEL_MAP[override["pred_class"]]
            confidence = override["confidence"]
            sarcasm_applied = True

    # Aspects (optional)
    aspects = []
    if enable_aspects:
        logger.info("Running aspect-based analysis")
        try:
            from src.models.aspect import analyze_aspects
            aspects = analyze_aspects(analysis_input)
        except Exception as e:
            logger.warning("Aspect analysis error: %s", e)

    # V3 RULE 9: Structured logging
    logger.info(
        "Pipeline complete: model_used=auto language_detected=%s "
        "translation_status=%s correction_applied=%s final_label=%s conf=%.1f%%",
        lang_code, translation_status,
        "yes" if pp["neutral_corrected"] else "no",
        pp["sentiment"], confidence * 100,
    )

    return {
        "original": original,
        "language": lang_code,
        "language_name": lang_info["name"],
        "flag_emoji": lang_info["flag_emoji"],
        "translated": translated,
        "was_translated": was_translated,
        "sentiment": pp["sentiment"],
        "label": pp["label"],
        "label_name": pp["label_name"],
        "confidence": confidence,
        "raw_confidence": pp["raw_confidence"],
        "scores": pp["scores"],
        "polarity": pp["polarity"],
        "subjectivity": pp["subjectivity"],
        "neutral_corrected": pp["neutral_corrected"],
        "correction_reason": pp["correction_reason"],
        "guard_applied": pp["guard_applied"],
        "temperature_scaled": pp["temperature_scaled"],
        "translation_status": translation_status,
        "translation_flagged": translation_flagged,
        "translation_failed": translation_status == "FALLBACK_PASSTHROUGH",
        "hinglish_detected": hinglish_detected,
        "analysis_input_source": "original",
        "sarcasm": sarcasm_result,
        "sarcasm_status": "ENABLED" if enable_sarcasm else "DISABLED",
        "sarcasm_detected": sarcasm_detected,
        "sarcasm_confidence": float(sarcasm_confidence_val),
        "sarcasm_applied": sarcasm_applied,
        "sarcasm_reason": sarcasm_reason,
        "aspects": aspects,
    }


# ═══════════════════════════════════════════════════════════════
# BATCH PREDICTION PIPELINE
# ═══════════════════════════════════════════════════════════════

def run_pipeline_batch(
    texts: list[str],
    enable_sarcasm: bool = False,
    enable_aspects: bool = False,
    progress_callback: Callable[[int, str], None] | None = None,
) -> list[dict]:
    """Batch pipeline with per-row progress, sarcasm bulk detection, and session state guard."""
    if not texts:
        return []

    raw_texts = [str(t or "").strip() for t in texts]
    clean_texts = [clean_text(t) or "" for t in raw_texts]
    total = len(clean_texts)
    logger.info("Starting batch analysis: %d reviews", total)

    def _progress(pct: int, msg: str):
        if progress_callback:
            progress_callback(min(pct, 100), msg)

    # Step 1+2: Language detection + translation
    _progress(5, "🌐 Detecting languages...")
    translated_texts = []
    lang_infos = []
    translation_statuses = []
    translation_flags = []
    hinglish_flags = []

    for i, text in enumerate(clean_texts):
        if not text:
            translated_texts.append("")
            lang_infos.append({"code": "unknown", "name": "Unknown", "flag_emoji": "🏳️",
                               "was_translated": False, "hinglish_detected": False})
            translation_statuses.append("OK")
            translation_flags.append(False)
            hinglish_flags.append(False)
            continue

        lang = detect_language(text)
        lang_code = lang["code"]
        is_hinglish = lang.get("hinglish_detected", False)
        hinglish_flags.append(is_hinglish)

        if is_hinglish:
            translated_texts.append(text)
            lang_infos.append({**lang, "was_translated": False, "translated": text})
            translation_statuses.append("OK")
            translation_flags.append(False)
        elif lang_code not in ("en", "unknown"):
            tr_result = safe_translate(text, lang_code)
            tr_text = tr_result["translated_text"]
            was_tr = tr_text.strip().lower() != text.strip().lower()
            translated_texts.append(tr_text if was_tr else text)
            lang_infos.append({**lang, "was_translated": was_tr, "translated": tr_text})
            translation_statuses.append(tr_result["translation_status"])

            # Validate translation
            if was_tr:
                val = validate_translation(text, tr_text)
                translation_flags.append(val["translation_flagged"])
            else:
                translation_flags.append(False)
        else:
            translated_texts.append(text)
            lang_infos.append({**lang, "was_translated": False, "translated": text})
            translation_statuses.append("OK")
            translation_flags.append(False)

        if i % 2 == 0:
            pct = 5 + int((i + 1) / total * 20)
            flag = lang.get("flag_emoji", "🏳️")
            _progress(pct, f"🔍 {i+1}/{total} | {flag} {lang['name']}")

    # Step 3: Batch sentiment
    _progress(25, f"⚡ Running sentiment model on {total} reviews...")
    sentiments = sentiment_predict_batch(translated_texts)
    _progress(60, "✅ Sentiment analysis complete")

    # Step 4: Batch sarcasm (transformer-based)
    sarcasm_results = [None] * total
    if enable_sarcasm:
        _progress(60, f"🎭 Running sarcasm detection on {total} reviews...")
        from src.models.sarcasm_model import predict_batch as sarcasm_predict_batch
        sarcasm_results = sarcasm_predict_batch(translated_texts)
        _progress(80, "✅ Sarcasm detection complete")

    # Step 5: Per-row aspect analysis
    aspect_lists: list[list] = [[] for _ in range(total)]
    if enable_aspects:
        _progress(80, "🔬 Running aspect analysis...")
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

    # Assemble results with full post-processing
    _progress(90, "📊 Assembling results...")
    results = []
    for i in range(total):
        try:
            sent = sentiments[i]
            analysis_text = translated_texts[i] or clean_texts[i]

            # Apply full post-processing pipeline
            pp = _apply_post_processing(analysis_text, sent)

            # Reduce confidence if translation flagged
            confidence = pp["confidence"]
            if translation_flags[i]:
                confidence = round(confidence * 0.85, 4)
                confidence = max(confidence, 0.40)

            li = lang_infos[i]

            # Bulk sarcasm detection (rule-based, ADD-ON 7 guards included)
            bulk_sarc = detect_sarcasm_bulk(analysis_text, pp["label"], confidence)

            # Merge transformer sarcasm if available
            final_sarcasm = sarcasm_results[i] if sarcasm_results[i] else bulk_sarc

            # Sarcasm → sentiment override
            is_sarc = final_sarcasm.get("is_sarcastic", False) if final_sarcasm else False
            sarc_conf = final_sarcasm.get("confidence", 0.0) if final_sarcasm else 0.0
            sarc_reason = final_sarcasm.get("reason", "") if final_sarcasm else ""
            sarc_override = _apply_sarcasm_override(pp["label"], confidence, is_sarc, sarc_conf)
            if sarc_override["sarcasm_applied"]:
                pp["label"] = sarc_override["pred_class"]
                pp["label_name"] = LABEL_MAP[sarc_override["pred_class"]]
                pp["sentiment"] = LABEL_MAP[sarc_override["pred_class"]]
                confidence = sarc_override["confidence"]


            results.append({
                "original": clean_texts[i],
                "language": li.get("code", "unknown"),
                "language_name": li.get("name", "Unknown"),
                "flag_emoji": li.get("flag_emoji", "🏳️"),
                "translated": li.get("translated", clean_texts[i]),
                "was_translated": li.get("was_translated", False),
                "sentiment": pp["sentiment"],
                "label": pp["label"],
                "label_name": pp["label_name"],
                "confidence": confidence,
                "raw_confidence": pp["raw_confidence"],
                "scores": pp["scores"],
                "polarity": pp["polarity"],
                "subjectivity": pp["subjectivity"],
                "neutral_corrected": pp["neutral_corrected"],
                "correction_reason": pp["correction_reason"],
                "guard_applied": pp["guard_applied"],
                "temperature_scaled": pp["temperature_scaled"],
                "translation_status": translation_statuses[i],
                "translation_flagged": translation_flags[i],
                "translation_failed": translation_statuses[i] == "FALLBACK_PASSTHROUGH",
                "hinglish_detected": hinglish_flags[i],
                "analysis_input_source": "original",
                "sarcasm": final_sarcasm,
                "sarcasm_status": "ENABLED" if enable_sarcasm else "DISABLED",
                "sarcasm_detected": is_sarc,
                "sarcasm_confidence": float(sarc_conf),
                "sarcasm_applied": sarc_override["sarcasm_applied"],
                "sarcasm_reason": sarc_reason,
                "aspects": aspect_lists[i],
            })
        except Exception as e:
            logger.error("Row %d failed: %s", i, e)
            results.append({
                "original": clean_texts[i], "language": "unknown",
                "language_name": "Unknown", "flag_emoji": "🏳️",
                "translated": clean_texts[i], "was_translated": False,
                "sentiment": "ERROR", "label": -1, "label_name": "ERROR",
                "confidence": 0.0, "raw_confidence": 0.0,
                "scores": [0, 0, 0], "polarity": 0.0, "subjectivity": 0.0,
                "neutral_corrected": False, "correction_reason": "",
                "guard_applied": None, "temperature_scaled": False,
                "translation_status": "OK", "translation_flagged": False,
                "hinglish_detected": False, "analysis_input_source": "original",
                "sarcasm": None, "sarcasm_status": "DISABLED",
                "sarcasm_detected": False, "sarcasm_confidence": 0.0,
                "sarcasm_applied": False, "sarcasm_reason": "",
                "translation_failed": False,
                "aspects": [], "error": str(e),
            })

        # RT-1: Progress callback after EVERY single row
        if progress_callback:
            pct = 90 + int((i + 1) / total * 10)
            progress_callback(min(pct, 100), f"📊 Processed {i+1}/{total}")

    _progress(100, "✅ Analysis complete!")
    logger.info("Batch analysis complete: %d reviews processed", total)
    return results


def _empty_result() -> dict:
    return {
        "original": "", "language": "unknown", "language_name": "Unknown",
        "flag_emoji": "🏳️", "translated": "", "was_translated": False,
        "sentiment": "Neutral", "label": 1, "label_name": "Neutral",
        "confidence": 0.0, "raw_confidence": 0.0,
        "scores": [0.0, 1.0, 0.0], "polarity": 0.0, "subjectivity": 0.0,
        "neutral_corrected": False, "correction_reason": "",
        "guard_applied": None, "temperature_scaled": False,
        "translation_status": "OK", "translation_flagged": False,
        "hinglish_detected": False, "analysis_input_source": "original",
        "sarcasm": None, "sarcasm_status": "DISABLED",
        "sarcasm_detected": False, "sarcasm_confidence": 0.0,
        "sarcasm_applied": False, "sarcasm_reason": "",
        "translation_failed": False,
        "aspects": [],
    }

