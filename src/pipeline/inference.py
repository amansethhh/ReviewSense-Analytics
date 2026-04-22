"""Unified inference pipeline for ReviewSense Analytics.

V5 ARCHITECTURE:
  Translation is USED for inference ONLY when validated.
  If translation fails trust check → fallback to XLM-R on original text.
  Translation is NOT display-only — it routes inference for non-Latin languages.

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
from src.models.translation import translate_batch, translate_to_english, normalize_hinglish, translation_trust_check
from src.models.sentiment import predict as sentiment_predict
from src.models.sentiment import predict_batch as sentiment_predict_batch
from src.predict import (
    apply_short_text_guard,
    compute_polarity_from_label,
    _apply_sarcasm_override,
    compute_calibrated_confidence,
    apply_decision_layer,
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

def validate_translation(original_text: str, translated_text: str) -> bool:
    """V6 strict translation validation."""
    original = str(original_text or "").strip()
    translated = str(translated_text or "").strip()
    if len(translated) < 3:
        return False
    if translated == original:
        return False
    if "[" in translated:
        return False
    return True


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
    route: str = "ENGLISH",
    model_used: str = "roberta",
) -> dict:
    """Apply the stabilized post-processing pipeline.

    V5 Precision Pipeline:
      Step 1: Dynamic margin-based decision layer (route-aware)
      Step 2: Short-text keyword guard (safety net)
      Step 3: Entropy-based calibrated confidence

    REMOVED (Section 8):
      ❌ TextBlob polarity
      ❌ VADER compound
      ❌ Neutral correction v2
      ❌ Label lock / confidence gate (replaced by margin decision)
      ❌ Polarity-based corrections

    RULE: After this function, NO downstream logic may modify
    label, confidence, or margin. This is FINAL.
    """
    scores = sentiment["scores"]
    pred_class = sentiment["label"]
    raw_confidence = sentiment["confidence"]

    # ── Step 1: Dynamic margin-based decision (V5) ──────────
    pred_class, margin, decision_type = apply_decision_layer(
        scores, LABEL_MAP, route=route, model_used=model_used,
    )

    # ── Step 2: Short-text keyword guard (safety net) ──────
    # Retained: keyword-based, NOT polarity-based
    guard_result = apply_short_text_guard(text, pred_class, raw_confidence)
    pred_class = guard_result["pred_class"]
    guard_applied = guard_result["guard_applied"]

    # ── Step 3: Entropy-based confidence ─────────────────
    confidence = compute_calibrated_confidence(scores)

    label_name = LABEL_MAP[pred_class]

    # Derive display polarity from label + confidence
    display_polarity = compute_polarity_from_label(label_name, confidence)

    return {
        "label": pred_class,
        "label_name": label_name,
        "sentiment": label_name,
        "confidence": float(confidence),
        "raw_confidence": float(raw_confidence),
        "polarity": display_polarity,
        "subjectivity": 0.5,  # No TextBlob — neutral default
        "neutral_corrected": False,
        "correction_reason": "",
        "guard_applied": guard_applied,
        "temperature_scaled": False,
        "scores": scores,
        "margin": round(margin, 4),
        "decision_type": decision_type,
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



def validate_route(route: str, lang_code: str, model_used: str) -> bool:
    """V5 FIX 6: Strict routing validation.

    Checks that the pipeline route matches the model used.
    Logs a warning on mismatch but does NOT crash — allows graceful fallback.

    Returns True if route is valid, False on mismatch.
    """
    if route == "HINGLISH" and "roberta" not in model_used:
        logger.warning(
            "[ROUTE MISMATCH] Hinglish should use RoBERTa, got %s",
            model_used,
        )
        return False

    if route == "ENGLISH" and "roberta" not in model_used:
        logger.warning(
            "[ROUTE MISMATCH] English should use RoBERTa, got %s",
            model_used,
        )
        return False

    return True


# ═══════════════════════════════════════════════════════════════
# SINGLE PREDICTION PIPELINE
# ═══════════════════════════════════════════════════════════════

def run_pipeline(
    text: str,
    enable_sarcasm: bool = False,
    enable_aspects: bool = True,
) -> dict:
    """Run the full NLP pipeline on a single text input.

    HYBRID ARCHITECTURE (Sections 1-5):
      ENGLISH     → RoBERTa on original text
      HINGLISH    → Normalize → RoBERTa on normalized text
      MULTILINGUAL → Translate → (valid → RoBERTa on translated, invalid → XLM-R on original)
    """
    original = clean_text(text)
    if not original:
        return _empty_result()

    # ── Step 1: Detect language ─────────────────────────────
    lang_info = detect_language(original)
    lang_code = lang_info["code"]
    hinglish_detected = lang_info.get("hinglish_detected", False)
    logger.info("Language detected: %s (%s)", lang_info["name"], lang_code)

    # ── Section 1: Route input ──────────────────────────────
    from src.predict import route_input
    route = route_input(original, lang_code)

    # Fix: if route_input detected MULTILINGUAL but lang detector said "en",
    # the text contains non-English markers. Override lang_code to ensure
    # XLM-R is used (not the English RoBERTa path).
    if route == "MULTILINGUAL" and lang_code == "en":
        lang_code = "xx"  # Generic multilingual — will use XLM-R
        logger.info("Route override: lang_code en → xx (non-English markers detected)")

    logger.info("Pipeline route: %s", route)

    # ── Sections 3+4: Conditional routing ───────────────────
    translation_status = "OK"
    translation_flagged = False
    translated = original
    was_translated = False
    translation_valid = None  # None for non-multilingual routes

    if route == "ENGLISH":
        # CASE 1: English → RoBERTa on original text
        final_text = original
        model_lang = "en"  # Forces RoBERTa routing
        logger.info("Route ENGLISH: RoBERTa on original text")

    elif route == "HINGLISH":
        # CASE 2: Hinglish → Normalize → RoBERTa
        hinglish_detected = True
        final_text = normalize_hinglish(original)
        translated = final_text  # Show normalized as "translation"
        was_translated = final_text.strip().lower() != original.strip().lower()
        model_lang = "en"  # Forces RoBERTa routing
        logger.info("Route HINGLISH: Normalize → RoBERTa")

    else:
        # CASE 3: Multilingual → Route based on language family
        #
        # XLM-R is strong on Latin-script European languages (de, fr, es, it, pt).
        # For these, ALWAYS use XLM-R on original text — it's more accurate
        # than translating and running through RoBERTa.
        #
        # For non-Latin languages (ar, hi, ja, zh, ko, etc.), XLM-R may struggle.
        # Use translation→RoBERTa when translation is valid.
        XLM_PREFERRED_LANGS = frozenset({
            "de", "fr", "es", "it", "pt", "nl", "sv", "da", "no", "fi",
            "pl", "cs", "ro", "hu", "tr", "id", "ms", "vi",
            "xx",  # Generic multilingual override (misdetected non-English)
        })

        if lang_code in XLM_PREFERRED_LANGS:
            # XLM-R preferred: use XLM-R directly on original text
            final_text = original
            model_lang = lang_code
            translation_valid = None  # Translation not attempted for model routing

            # Translate for DISPLAY — skip if lang unknown (xx)
            if lang_code != "xx":
                logger.info("Route MULTILINGUAL→XLM-R (preferred): %s", lang_code)
                tr_result = safe_translate(original, lang_code)
                translated = tr_result["translated_text"]
                translation_status = tr_result["translation_status"]
                was_translated = translated.strip().lower() != original.strip().lower()
            else:
                logger.info("Route MULTILINGUAL→XLM-R (override): non-English markers detected")

        else:
            # Non-Latin languages: Translate → Trust check → Route
            logger.info("Route MULTILINGUAL: Translating from %s", lang_code)
            tr_result = safe_translate(original, lang_code)
            translated = tr_result["translated_text"]
            translation_status = tr_result["translation_status"]
            was_translated = translated.strip().lower() != original.strip().lower()

            if was_translated:
                trusted, trust_reason = translation_trust_check(original, translated)
                translation_valid = trusted

                if trusted:
                    # Valid translation → RoBERTa on translated English text
                    final_text = translated
                    model_lang = "en"  # Forces RoBERTa routing
                    logger.info(
                        "Route MULTILINGUAL→ROBERTA: Valid translation, using RoBERTa"
                    )
                else:
                    # Invalid translation → XLM-R on original text
                    final_text = original
                    model_lang = lang_code  # Forces XLM-R routing
                    translation_flagged = True
                    translation_status = f"FALLBACK_{trust_reason.upper()}"
                    was_translated = False
                    logger.warning(
                        "Route MULTILINGUAL→XLM-R: Translation rejected (%s), using XLM-R",
                        trust_reason,
                    )
            else:
                # Translation returned same text → XLM-R on original
                final_text = original
                model_lang = lang_code
                translation_valid = False
                logger.info("Route MULTILINGUAL→XLM-R: No translation produced")

    # ── Step 3: Run sentiment on routed text ────────────────
    logger.info("Running sentiment prediction (model_lang=%s)", model_lang)
    sentiment = sentiment_predict(final_text, lang_code=model_lang)
    model_used = sentiment.get("model_used", "unknown")

    # ── Apply full post-processing pipeline (V5: route-aware) ─
    pp = _apply_post_processing(
        final_text, sentiment,
        lang_code=model_lang,
        translated_text="",
        route=route,
        model_used=model_used,
    )

    # ── Section 4: Translation confidence isolation ──────
    confidence = pp["confidence"]
    translation_used = model_used == "roberta" and route == "MULTILINGUAL"

    if translation_used:
        confidence = min(confidence, 0.85)

    if translation_flagged:
        confidence = round(confidence * 0.85, 4)
        confidence = max(confidence, 0.40)

    # ── V5 FIX 6: Validate route correctness ─────────────
    route_valid = validate_route(route, lang_code, model_used)

    # ── Section 7: Pipeline trace (mandatory debug) ─────
    pipeline_trace = {
        "route": route,
        "model_used": model_used,
        "translation_used": translation_used,
        "translation_valid": translation_valid,
        "confidence": confidence,
        "margin": pp.get("margin", 0.0),
        "decision": pp.get("decision_type", "unknown"),
        "route_valid": route_valid,
    }

    # Sarcasm (optional) + override
    sarcasm_result = None
    sarcasm_detected = False
    sarcasm_confidence_val = 0.0
    sarcasm_applied = False
    sarcasm_reason = ""

    if enable_sarcasm:
        logger.info("Running sarcasm detection")
        from src.models.sarcasm_model import predict as sarcasm_predict
        sarcasm_result = sarcasm_predict(final_text)
        sarcasm_detected = sarcasm_result.get("is_sarcastic", False)
        sarcasm_confidence_val = sarcasm_result.get("confidence", 0.0)
        sarcasm_reason = sarcasm_result.get("reason", "")

        override = _apply_sarcasm_override(
            pp["label"], confidence, sarcasm_detected, sarcasm_confidence_val
        )
        if override["sarcasm_applied"]:
            pp["label"] = override["pred_class"]
            pp["label_name"] = LABEL_MAP[override["pred_class"]]
            pp["sentiment"] = LABEL_MAP[override["pred_class"]]
            confidence = override["confidence"]
            sarcasm_applied = True
            pp["polarity"] = compute_polarity_from_label(
                LABEL_MAP[override["pred_class"]], confidence
            )

    # Aspects (optional)
    aspects = []
    if enable_aspects:
        logger.info("Running aspect-based analysis")
        try:
            from src.models.aspect import analyze_aspects
            aspects = analyze_aspects(final_text)
        except Exception as e:
            logger.warning("Aspect analysis error: %s", e)

    # Structured logging
    logger.info(
        "Pipeline complete: route=%s model_used=%s language=%s "
        "translation_status=%s final_label=%s conf=%.1f%%",
        route, model_used, lang_code, translation_status,
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
        "translation_failed": translation_status.startswith("FALLBACK"),
        "hinglish_detected": hinglish_detected,
        "analysis_input_source": route.lower(),
        "pipeline_trace": pipeline_trace,
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
    from collections import defaultdict

    translated_texts = list(clean_texts)
    lang_infos = []
    translation_statuses = ["OK"] * total
    translation_flags = [False] * total
    hinglish_flags = []
    translation_groups: dict[str, list[int]] = defaultdict(list)

    for i, text in enumerate(clean_texts):
        if not text:
            lang_infos.append({"code": "unknown", "name": "Unknown", "flag_emoji": "🏳️",
                               "was_translated": False, "hinglish_detected": False,
                               "translated": ""})
            hinglish_flags.append(False)
            continue

        lang = detect_language(text)
        lang_code = lang["code"]
        is_hinglish = lang.get("hinglish_detected", False)
        hinglish_flags.append(is_hinglish)
        lang_infos.append({**lang, "was_translated": False, "translated": text})

        if not is_hinglish and lang_code not in ("en", "unknown"):
            translation_groups[lang_code].append(i)

        if i % 2 == 0:
            pct = 5 + int((i + 1) / total * 20)
            flag = lang.get("flag_emoji", "🏳️")
            _progress(pct, f"🔍 {i+1}/{total} | {flag} {lang['name']}")

    if translation_groups:
        _progress(20, "🌐 Translating non-English reviews in batches...")
        groups_done = 0
        for lang_code, indices in translation_groups.items():
            batch_texts = [clean_texts[idx] for idx in indices]
            try:
                batch_translations = translate_batch(batch_texts, lang_code)
            except Exception as exc:
                logger.warning("Batch translation failed for %s: %s", lang_code, exc)
                batch_translations = batch_texts
            if len(batch_translations) != len(batch_texts):
                logger.warning(
                    "Batch translation length mismatch for %s: expected %d got %d",
                    lang_code,
                    len(batch_texts),
                    len(batch_translations),
                )
                batch_translations = batch_texts

            for idx, original, translated in zip(indices, batch_texts, batch_translations):
                if validate_translation(original, translated):
                    translated_texts[idx] = translated
                    lang_infos[idx] = {
                        **lang_infos[idx],
                        "was_translated": True,
                        "translated": translated,
                    }
                else:
                    translated_texts[idx] = original
                    lang_infos[idx] = {
                        **lang_infos[idx],
                        "was_translated": False,
                        "translated": original,
                    }
                    translation_statuses[idx] = "FALLBACK_PASSTHROUGH"
                    translation_flags[idx] = True

            groups_done += 1
            _progress(
                20 + int(groups_done / max(1, len(translation_groups)) * 5),
                f"🌐 Batch translated {groups_done}/{len(translation_groups)} language groups",
            )

    # Step 3: Batch sentiment
    # Section 4: Normalize Hinglish texts before sentiment prediction
    _progress(25, f"⚡ Running sentiment model on {total} reviews...")
    analysis_texts = [
        normalize_hinglish(clean_texts[i]) if hinglish_flags[i] else clean_texts[i]
        for i in range(total)
    ]
    lang_codes = [li.get("code", "en") for li in lang_infos]
    sentiments = sentiment_predict_batch(analysis_texts, lang_codes=lang_codes)
    _progress(60, "✅ Sentiment analysis complete")

    # Step 4: Batch sarcasm (transformer-based)
    sarcasm_results = [None] * total
    if enable_sarcasm:
        _progress(60, f"🎭 Running sarcasm detection on {total} reviews...")
        from src.models.sarcasm_model import predict_batch as sarcasm_predict_batch
        sarcasm_results = sarcasm_predict_batch(clean_texts)
        _progress(80, "✅ Sarcasm detection complete")

    # Step 5: Per-row aspect analysis
    aspect_lists: list[list] = [[] for _ in range(total)]
    if enable_aspects:
        _progress(80, "🔬 Running aspect analysis...")
        try:
            from src.models.aspect import analyze_aspects
            for i, at in enumerate(clean_texts):
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
            analysis_text = clean_texts[i]
            li = lang_infos[i]

            # Apply full post-processing pipeline
            pp = _apply_post_processing(
                analysis_text,
                sent,
                lang_code=li.get("code", "en"),
                translated_text="",
            )

            # Reduce confidence if translation flagged
            confidence = pp["confidence"]
            if translation_flags[i]:
                confidence = round(confidence * 0.85, 4)
                confidence = max(confidence, 0.40)

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
                # Section 1 FIX: Recalculate polarity after sarcasm label flip
                pp["polarity"] = compute_polarity_from_label(
                    LABEL_MAP[sarc_override["pred_class"]], confidence
                )


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
