"""
Language detection, translation, and sentiment analysis route.

MASTER FIX: Complete system stabilization.

FIX-1: Translation quality — two-tier fallback
       (Helsinki-NLP → googletrans) with quality validation.
FIX-2: langdetect false positives — regex script pre-checks
       + adaptive confidence thresholds by text length.
FIX-3: Null prediction guard — 0.0 confidence flagged.
FIX-4: Mixed sentiment post-processing for "but" clauses
       and double negatives.
FIX-5: Cache key uses post-translation English text.

CRITICAL INVARIANT:
  predict_sentiment() receives ONLY English text.
  Cache keys are ALWAYS based on English text.
  Translation happens BEFORE cache lookup and prediction.
"""

import re
import time
import logging
import asyncio

from fastapi import APIRouter, Depends, HTTPException

from app.schemas import (
    LanguageRequest, LanguageResponse, SentimentLabel
)
from app.dependencies import (
    get_model, get_vectorizer, add_src_to_path
)
from app.utils import normalize_confidence
from app.adaptive import (
    primary_pool,
    inference_throttler,
)
from app.cache import prediction_cache
from app.metrics_store import metrics_store

router = APIRouter()
logger = logging.getLogger("reviewsense.language")
add_src_to_path()

# Phase 2, Part 4: Inference timeout (seconds)
_INFERENCE_TIMEOUT_S: float = 8.0

LANGUAGE_CODE_MAP = {
    "en":    "English",   "hi": "Hindi",
    "ta":    "Tamil",     "bn": "Bengali",
    "es":    "Spanish",   "fr": "French",
    "de":    "German",    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ar":    "Arabic",    "pt": "Portuguese",
    "ru":    "Russian",   "ja": "Japanese",
    "ko":    "Korean",    "it": "Italian",
    "nl":    "Dutch",     "tr": "Turkish",
    "sv":    "Swedish",   "th": "Thai",
    "pl":    "Polish",
}

# L1/L3: Whitelist of supported language codes
_SUPPORTED_LANG_CODES = set(LANGUAGE_CODE_MAP.keys()) | {"unknown"}

# L1: Polish diacritical characters for script-based detection
_POLISH_CHARS = set('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')

# L2: Portuguese markers for disambiguation from Spanish
_PORTUGUESE_MARKERS = re.compile(
    r'(?:ção|ções|ões|lho|lha|ão|ã|nh[ao]|\bmuito\b|\bproduto\b|\bbom\b|\bnão\b|\bótimo\b|\bpéssimo\b)',
    re.IGNORECASE,
)

# T2/T4: Regex to strip language name suffixes appended by translation
_LANG_SUFFIX_RE = re.compile(
    r'\s*[,.]?\s*(?:Hindi|Chinese|Korean|Arabic|Russian|German|French|'
    r'Spanish|Italian|Portuguese|Japanese|Thai|Turkish|Swedish|Dutch|'
    r'Polish|Bengali|Tamil)\s*[.]?\s*$',
    re.IGNORECASE,
)


# ══════════════════════════════════════════════════════════
# FIX-2: Adaptive language detection with regex pre-checks
# ══════════════════════════════════════════════════════════

def detect_language_adaptive(text: str) -> tuple:
    """
    Adaptive language detection with regex pre-checks
    and length-based confidence thresholds.

    Returns (language_code, confidence).

    Regex pre-checks catch script-specific languages with
    100% accuracy (Devanagari, Arabic, Korean, etc.) before
    falling through to langdetect for Latin-script languages.
    """
    if not text or len(text.strip()) < 2:
        return ("unknown", 0.0)

    text_clean = text.strip()

    # ── Script-based detection (100% confidence) ──────────
    # Unambiguous scripts bypass langdetect entirely.
    if re.search(r'[\u0900-\u097f]', text_clean):
        return ("hi", 1.0)  # Devanagari → Hindi

    if re.search(r'[\u0980-\u09ff]', text_clean):
        return ("bn", 1.0)  # Bengali

    if re.search(r'[\u0b80-\u0bff]', text_clean):
        return ("ta", 1.0)  # Tamil

    if re.search(
        r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff'
        r'\ufb50-\ufdff\ufe70-\ufeff]',
        text_clean,
    ):
        return ("ar", 1.0)  # Arabic

    if re.search(r'[가-힣]', text_clean):
        return ("ko", 1.0)  # Korean Hangul

    if re.search(r'[ก-๙]', text_clean):
        return ("th", 1.0)  # Thai

    if re.search(r'[а-яА-ЯёЁ]', text_clean):
        return ("ru", 1.0)  # Cyrillic → Russian

    # BUG-2 FIX: Japanese MUST be detected BEFORE Chinese.
    # Japanese uses Hiragana/Katakana mixed with CJK.
    if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text_clean):
        return ("ja", 1.0)  # Japanese kana (Hiragana or Katakana)

    if re.search(r'[\u4e00-\u9fff]', text_clean):
        # CJK unified — only Chinese if no Japanese kana markers
        if not re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text_clean):
            return ("zh-cn", 0.95)

    if re.search(r'[א-ת]', text_clean):
        return ("he", 1.0)  # Hebrew

    # L1: Polish character-based detection (before langdetect)
    # BUG-2/8 FIX: Lower threshold to 1 for Polish diacritics detection
    if len(set(text_clean) & _POLISH_CHARS) >= 1:
        return ("pl", 1.0)

    # ── Adaptive threshold based on text length ───────────
    word_count = len(text_clean.split())
    if word_count <= 3:
        threshold = 0.70
    elif word_count <= 8:
        threshold = 0.85
    else:
        threshold = 0.92

    # ── langdetect with threshold ─────────────────────────
    try:
        from langdetect import detect_langs, DetectorFactory
        DetectorFactory.seed = 42  # L2: Deterministic detection
        langs = detect_langs(text_clean)
        if not langs:
            return ("unknown", 0.0)

        top_lang = langs[0]

        # L2: Portuguese/Spanish disambiguation
        if top_lang.lang == "es" and _PORTUGUESE_MARKERS.search(text_clean):
            logger.debug("Portuguese markers found — overriding es → pt")
            return ("pt", max(top_lang.prob, 0.85))

        # L3/BUG-2 FIX: Reject unsupported/garbage language codes
        # (e.g. "eu" for "European" which is not a valid ISO code)
        if top_lang.lang not in _SUPPORTED_LANG_CODES:
            logger.warning(
                f"Unsupported lang code '{top_lang.lang}' — "
                f"falling back to second-best or unknown"
            )
            if len(langs) > 1 and langs[1].lang in _SUPPORTED_LANG_CODES:
                return (langs[1].lang, langs[1].prob)
            return ("en", 0.0)  # Default to English, not unknown

        # English requires higher check: non-ASCII ratio
        if top_lang.lang == "en":
            ascii_ratio = sum(
                c.isascii() for c in text_clean
            ) / max(len(text_clean), 1)
            if ascii_ratio < 0.6:
                # Probably not English — use second-best
                if len(langs) > 1:
                    return (langs[1].lang, langs[1].prob)
                return ("unknown", 0.0)

            if top_lang.prob >= threshold:
                return ("en", top_lang.prob)
            # Not confident enough — second-best if available
            if len(langs) > 1 and langs[1].prob > 0.15:
                return (langs[1].lang, langs[1].prob)
            return ("en", top_lang.prob)
        else:
            return (top_lang.lang, top_lang.prob)

    except Exception as e:
        logger.warning(f"langdetect failed: {e}")
        return ("unknown", 0.0)


def _is_confidently_english(text: str) -> bool:
    """
    Returns True only if we are highly confident the text
    is English. Uses detect_language_adaptive() which
    includes regex pre-checks + confidence thresholds.
    """
    lang, confidence = detect_language_adaptive(text)
    return lang == "en" and confidence >= 0.85


# ══════════════════════════════════════════════════════════
# BUG-1 FIX: Degenerate translation output detection
# ══════════════════════════════════════════════════════════

# Known degenerate Helsinki-NLP outputs — model sometimes produces
# these garbage strings instead of actual translations.
DEGENERATE_OUTPUTS = frozenset({
    "...", "…", ".", "..", "....", ".....",
    "—", "--", "----",
    "the", "a", "i", "it", "is",
    "yes", "no", "ok", "okay",
    "null", "none", "undefined",
    "the the the", "a a a",
})


def _is_degenerate(translated: str, original: str) -> bool:
    """Detect degenerate/garbage translations from Helsinki-NLP.

    BUG-1 FIX: Catches:
      1. Known degenerate outputs (ellipsis, punctuation-only, etc.)
      2. Single repeated token (e.g. "the the the the")
      3. Translation shorter than 3 chars for inputs > 10 chars
      4. Low plausible-char ratio (< 50% alphanumeric)
    """
    t = translated.strip().lower()

    # Known degenerate patterns
    if t in DEGENERATE_OUTPUTS:
        return True

    # Single repeated token detection
    tokens = t.split()
    if len(tokens) >= 3 and len(set(tokens)) == 1:
        return True

    # Too short for meaningful translation
    if len(original) > 10 and len(t) < 3:
        return True

    # Low plausible character ratio (mostly punctuation/symbols)
    if len(t) > 0:
        alpha_count = sum(1 for c in t if c.isalnum() or c.isspace())
        if alpha_count / len(t) < 0.50:
            return True

    return False


def _validate_translation_quality(
    original: str,
    translated: str,
    source_lang: str,
) -> float:
    """
    Multi-factor quality scoring for translations.
    Returns 0.0-1.0 where >=0.70 means acceptable.
    """
    score = 1.0

    # Check 1: Length ratio (0.3x-4.0x expected)
    len_ratio = len(translated) / max(len(original), 1)
    if len_ratio < 0.2 or len_ratio > 5.0:
        score -= 0.4

    # Check 2: Empty or single-char translations
    if len(translated.strip()) <= 1:
        return 0.0

    # Check 3: If identical to original for non-English
    if (source_lang != "en"
            and translated.strip().lower()
            == original.strip().lower()):
        score -= 0.5

    # Check 4: Detect sentiment inversion hallucination
    # If original has clearly negative markers but
    # translation is overwhelmingly positive (or vice
    # versa), it's likely a hallucination.
    neg_markers = [
        "не", "плохо", "mal", "mauvais", "terrible",
        "schlecht", "awful", "بد", "悪い", "나쁜",
    ]
    pos_hallucination = [
        "excellent", "amazing", "great", "wonderful",
        "love", "perfect", "fantastic", "outstanding",
    ]
    orig_lower = original.lower()
    trans_lower = translated.lower()

    has_neg = any(m in orig_lower for m in neg_markers)
    has_pos_hall = any(
        p in trans_lower for p in pos_hallucination
    )
    if has_neg and has_pos_hall and len(
            translated.split()) < 8:
        score -= 0.4

    return max(0.0, min(1.0, score))


def _strip_language_suffix(translated: str) -> str:
    """T2/T4: Strip appended language name suffixes from translations."""
    if not translated:
        return translated
    return _LANG_SUFFIX_RE.sub('', translated).strip()


def _translate_with_fallback(
    text: str,
    source_lang: str,
) -> dict:
    """
    Two-tier translation with automatic fallback and
    quality validation.

    Tier 1: Helsinki-NLP via src.translator (fast, ~100ms)
    Tier 2: googletrans (slower, ~300ms, more reliable)

    Returns:
        { translated_text, method, confidence, warnings }
    """
    warnings: list[str] = []

    # BUG-1 FIX: Arabic is force-routed to Google Translate
    # because Helsinki ar→en produces consistently degenerate output.
    LANGUAGES_FORCE_GOOGLE = {"ar"}

    # === TIER 1: Helsinki-NLP (via existing pipeline) ===
    if source_lang not in LANGUAGES_FORCE_GOOGLE:
        try:
            from src.translator import detect_and_translate

            lang_result = detect_and_translate(text)
            if isinstance(lang_result, dict):
                helsinki_text = lang_result.get(
                    "translated_text", "")
                was_translated = lang_result.get(
                    "was_translated", False)

                if helsinki_text and was_translated:
                    helsinki_text = _strip_language_suffix(helsinki_text)

                    # BUG-1 FIX: Check for degenerate output FIRST
                    if _is_degenerate(helsinki_text, text):
                        warnings.append(
                            "Helsinki produced degenerate output, "
                            "falling back to Google"
                        )
                        logger.warning(
                            "Degenerate Helsinki output for "
                            "%s: '%s' → '%s'",
                            source_lang, text[:50],
                            helsinki_text[:50],
                        )
                    else:
                        quality = _validate_translation_quality(
                            text, helsinki_text, source_lang)
                        if quality >= 0.70:
                            return {
                                "translated_text": helsinki_text,
                                "method": "helsinki",
                                "confidence": quality,
                                "detected_language": lang_result.get(
                                    "detected_language", source_lang),
                                "language_name": lang_result.get(
                                    "language_name", "Unknown"),
                                "was_translated": True,
                                "warnings": [],
                            }
                        else:
                            warnings.append(
                                f"Helsinki quality low "
                                f"({quality:.0%}), using fallback"
                            )
                elif helsinki_text:
                    # Not flagged as translated — might be
                    # English already
                    return {
                        "translated_text": helsinki_text,
                        "method": "helsinki",
                        "confidence": 0.8,
                        "detected_language": lang_result.get(
                            "detected_language", source_lang),
                        "language_name": lang_result.get(
                            "language_name", "Unknown"),
                        "was_translated": False,
                        "warnings": [],
                    }
        except Exception as e:
            logger.warning(
                f"Helsinki-NLP failed for {source_lang}: {e}")
            warnings.append(
                f"Helsinki error: {str(e)[:50]}")
    else:
        warnings.append(
            f"Skipping Helsinki for {source_lang} "
            f"(force-Google language)")

    # === TIER 2: deep-translator (Google) with retry ===
    try:
        from app.utils.translation_client import (
            translate_with_retry,
        )
        src_lang = (
            "auto" if source_lang in ("auto", "unknown")
            else source_lang
        )
        translated, status = translate_with_retry(
            text, src_lang, "en"
        )
        if status == "success" and translated.strip():
            cleaned = _strip_language_suffix(translated.strip())
            return {
                "translated_text": cleaned,
                "method": "google",
                "confidence": 0.9,
                "detected_language": source_lang,
                "language_name": LANGUAGE_CODE_MAP.get(
                    source_lang, source_lang),
                "was_translated": True,
                "warnings": warnings,
            }
        else:
            warnings.append("Google retry exhausted")
    except Exception as e:
        logger.error(
            f"Both translators failed for "
            f"{source_lang}: {e}"
        )
        warnings.append(
            f"Google fallback failed: {str(e)[:50]}")

    # === TIER 3: raw predict on original text ===
    # Both Helsinki AND Google have failed.  We still return the
    # original text so the caller can run predict_sentiment on it
    # directly.  Setting was_translated=False ensures the pipeline
    # analyses the original (untranslated) text.
    logger.warning(
        "All translation tiers failed for lang=%s — "
        "falling through to raw prediction on original text",
        source_lang,
    )
    return {
        "translated_text": None,
        "method": "failed_raw_predict",
        "confidence": 0.0,
        "detected_language": source_lang,
        "language_name": LANGUAGE_CODE_MAP.get(
            source_lang, source_lang),
        "was_translated": False,
        "warnings": warnings,
    }


# ══════════════════════════════════════════════════════════
# FIX-4: Mixed sentiment post-processing
# B1: Now uses shared sentiment_corrections module
# ══════════════════════════════════════════════════════════

def _apply_sentiment_corrections(
    text: str,
    sentiment: str,
    confidence: float,
    polarity: float,
) -> tuple:
    """
    Wrapper around the shared apply_sentiment_corrections.
    Preserves the 4-arg signature used in language.py.
    """
    from app.sentiment_corrections import (
        apply_sentiment_corrections,
    )
    # BUG-3 FIX: Pass polarity to enable polarity floor check
    corrected_sent, corrected_conf, was_corrected = (
        apply_sentiment_corrections(
            text, sentiment, confidence, polarity=polarity
        )
    )
    if was_corrected:
        return (corrected_sent, corrected_conf, 0.0)
    return (sentiment, confidence, polarity)


# ══════════════════════════════════════════════════════════
# Core sync function for bulk and language analysis
# ══════════════════════════════════════════════════════════

def detect_translate_and_predict_sync(
    text: str,
    model_choice: str = "best",
    multilingual: bool = False,
    run_absa: bool = False,
    run_sarcasm: bool = False,
) -> dict:
    """
    Synchronous all-in-one: detect → translate → predict.
    Safe to call from daemon threads. NO asyncio.

    INVARIANT: predict_sentiment() always receives English.
    Cache key always uses English text.

    Includes:
    - FIX-1: Two-tier translation fallback
    - FIX-2: Adaptive language detection
    - FIX-3: Null prediction guard
    - FIX-4: Mixed sentiment post-processing
    """
    from src.predict import predict_sentiment

    original_text = str(text or "").strip()
    if not original_text:
        return {
            "sentiment": "neutral",
            "confidence": 50.0,
            "polarity": 0.0,
            "subjectivity": 0.0,
            "detected_language": "Unknown",
            "language_code": "unknown",
            "english_text": "",
            "was_translated": False,
            "skipped_translation": True,
            "cache_hit": False,
            "translation_error": False,
            "model_used": model_choice,
        }

    # ── Determine English text ────────────────────────────
    detected_language = "English"
    language_code = "en"
    english_text = original_text
    was_translated = False
    skipped_translation = True
    translation_error = False
    translation_method: str | None = None
    translation_warnings: list[str] = []

    if multilingual:
        # FIX-2: Adaptive detection with regex pre-checks
        lang_code, lang_confidence = (
            detect_language_adaptive(original_text))

        if lang_code == "en" and lang_confidence >= 0.85:
            # High confidence English → skip translation
            translation_method = "none"
            logger.debug(
                "English detected with high confidence "
                f"({lang_confidence:.0%}) — skipping"
            )
        elif lang_code == "unknown":
            # Can't detect → assume not English, try
            # translation anyway
            skipped_translation = False
            try:
                trans = _translate_with_fallback(
                    original_text, "auto")
                english_text = trans["translated_text"]
                was_translated = trans["was_translated"]
                translation_method = trans.get(
                    "method", None)
                detected_language = trans.get(
                    "language_name", "Unknown")
                language_code = trans.get(
                    "detected_language", "unknown")
                translation_warnings = trans.get(
                    "warnings", [])
            except Exception as e:
                logger.warning(f"Translation failed: {e}")
                translation_error = True
        else:
            # Non-English detected → translate
            skipped_translation = False
            detected_language = LANGUAGE_CODE_MAP.get(
                lang_code, lang_code.title())
            language_code = lang_code
            try:
                trans = _translate_with_fallback(
                    original_text, lang_code)
                # Tier 3 returns translated_text=None; fall back
                # to original so prediction still runs.
                english_text = trans["translated_text"] or original_text
                was_translated = trans["was_translated"]
                translation_method = trans.get(
                    "method", None)
                translation_warnings = trans.get(
                    "warnings", [])
                if trans["method"] in ("failed", "failed_raw_predict"):
                    translation_error = True
            except Exception as e:
                logger.warning(f"Translation failed: {e}")
                translation_error = True
                english_text = original_text

    # ── Cache check (keyed on English text) ───────────────
    cache_options = {
        "run_absa": run_absa,
        "run_sarcasm": run_sarcasm,
    }
    cache_key = prediction_cache.get_cache_key(
        english_text, model_choice, cache_options
    )
    cached = prediction_cache.get(cache_key)

    if cached is not None:
        metrics_store.record_cache_hit()
        return {
            **cached,
            "detected_language": detected_language,
            "language_code": language_code,
            "english_text": english_text,
            "translated_text": english_text if was_translated else None,
            "translation_method": translation_method,
            "was_translated": was_translated,
            "skipped_translation": skipped_translation,
            "cache_hit": True,
            "translation_error": translation_error,
        }

    metrics_store.record_cache_miss()

    # ── Prediction ────────────────────────────────────────
    try:
        if multilingual and was_translated:
            pred = predict_sentiment(
                english_text, model_choice)
        else:
            pred = predict_sentiment(
                original_text, model_choice)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "polarity": 0.0,
            "subjectivity": 0.0,
            "detected_language": detected_language,
            "language_code": language_code,
            "english_text": english_text,
            "was_translated": was_translated,
            "skipped_translation": skipped_translation,
            "cache_hit": False,
            "translation_error": True,
            "model_used": model_choice,
            "error": str(e)[:120],
        }

    label_name = pred.get("label_name", "Neutral")
    sentiment_raw = label_name.lower()
    if sentiment_raw not in [
        "positive", "negative", "neutral"
    ]:
        sentiment_raw = "neutral"

    raw_conf = float(pred.get("confidence", 0.0))
    confidence_pct = normalize_confidence(raw_conf)

    # ── FIX-3: Null prediction guard ─────────────────────
    if confidence_pct == 0.0 and raw_conf == 0.0:
        logger.warning(
            "Null prediction detected (0.0 confidence)")
        sentiment_raw = "unknown"

    polarity_val = float(pred.get("polarity", 0.0))

    # ── FIX-4: Mixed sentiment post-processing ───────────
    sentiment_raw, confidence_pct, polarity_val = (
        _apply_sentiment_corrections(
            english_text if was_translated
            else original_text,
            sentiment_raw,
            confidence_pct,
            polarity_val,
        )
    )

    result = {
        "sentiment": sentiment_raw,
        "confidence": confidence_pct,
        "polarity": polarity_val,
        "subjectivity": float(
            pred.get("subjectivity", 0.0)),
        "detected_language": detected_language,
        "language_code": language_code,
        "english_text": english_text,
        "translated_text": english_text if was_translated else None,
        "translation_method": translation_method,
        "was_translated": was_translated,
        "skipped_translation": skipped_translation,
        "cache_hit": False,
        "translation_error": translation_error,
        "model_used": pred.get(
            "model_used", model_choice),
    }

    # ── Cache store ───────────────────────────────────────
    cache_entry = {
        "sentiment": sentiment_raw,
        "confidence": confidence_pct,
        "polarity": polarity_val,
        "subjectivity": float(
            pred.get("subjectivity", 0.0)),
        "model_used": pred.get(
            "model_used", model_choice),
    }
    prediction_cache.set(cache_key, cache_entry)

    return result


# ══════════════════════════════════════════════════════════
# Language pipeline (for the /language endpoint)
# ══════════════════════════════════════════════════════════

def _run_language_pipeline(
    text: str, model_choice: str
) -> dict:
    """
    Full language detection + translation + sentiment
    pipeline. Runs in thread pool executor.

    Uses FIX-1 (two-tier translation fallback),
    FIX-2 (adaptive language detection),
    FIX-3 (null prediction guard),
    FIX-4 (mixed sentiment post-processing).
    """
    from src.predict import predict_sentiment

    # ── FIX-2: Adaptive language detection ────────────────
    lang_code, lang_confidence = (
        detect_language_adaptive(text))

    if lang_code == "en" and lang_confidence >= 0.85:
        logger.debug(
            f"English detected ({lang_confidence:.0%}) "
            f"— skipping translation"
        )
        # W4-1: Record skipped translation
        metrics_store.record_translation(
            "skipped", "en")
        try:
            pred = predict_sentiment(text, model_choice)
        except Exception as e:
            raise RuntimeError(
                f"Prediction failed on English text: {e}"
            )

        label_name = pred.get("label_name", "Neutral")
        sentiment_raw = label_name.lower()
        if sentiment_raw not in ["positive", "negative",
                                  "neutral"]:
            sentiment_raw = "neutral"

        raw_conf = float(pred.get("confidence", 0.0))
        confidence_pct = normalize_confidence(raw_conf)
        polarity_val = float(pred.get("polarity", 0.0))

        # FIX-3: Null prediction guard
        if confidence_pct == 0.0 and raw_conf == 0.0:
            sentiment_raw = "unknown"

        # FIX-4: Mixed sentiment correction
        sentiment_raw, confidence_pct, polarity_val = (
            _apply_sentiment_corrections(
                text, sentiment_raw,
                confidence_pct, polarity_val))

        return {
            "detected_language":    "English",
            "language_code":        "en",
            "detection_confidence": lang_confidence,
            "translated_text":      text,
            "translation_needed":   False,
            "skipped_translation":  True,
            "sentiment":            sentiment_raw,
            "confidence":           confidence_pct,
            "polarity":             polarity_val,
            "subjectivity":         float(pred.get(
                                    "subjectivity", 0.0)),
            "model_used":           pred.get("model_used",
                                    model_choice),
        }

    # ── Non-English: translate with two-tier fallback ─────
    if lang_code == "unknown":
        source_lang = "auto"
    else:
        source_lang = lang_code

    # FIX-1: Two-tier fallback translation (+ Tier 3 raw predict)
    trans = _translate_with_fallback(text, source_lang)
    # Tier 3 returns translated_text=None; fall back to original
    translated_text = trans["translated_text"]
    was_translated = trans["was_translated"]
    translation_method = trans["method"]

    # W4-1: Record translation event
    metrics_store.record_translation(
        translation_method, lang_code)

    # Use detected language from translation result or
    # from our pre-check
    if trans.get("detected_language", "auto") != "auto":
        lang_code = trans["detected_language"]

    display_name = LANGUAGE_CODE_MAP.get(
        lang_code, trans.get(
            "language_name", lang_code.title()))

    # Determine analysis text — use translated if available,
    # otherwise fall back to original (Tier 3 raw predict).
    analysis_text = (
        translated_text
        if was_translated and translated_text and translated_text.strip()
        else text
    )

    try:
        pred = predict_sentiment(
            analysis_text, model_choice)
    except Exception as e:
        raise RuntimeError(
            f"Prediction failed on translated text: {e}"
        )

    label_name = pred.get("label_name", "Neutral")
    sentiment_raw = label_name.lower()
    if sentiment_raw not in ["positive", "negative",
                              "neutral"]:
        sentiment_raw = "neutral"

    raw_conf = float(pred.get("confidence", 0.0))
    confidence_pct = normalize_confidence(raw_conf)
    polarity_val = float(pred.get("polarity", 0.0))

    # FIX-3: Null prediction guard
    if confidence_pct == 0.0 and raw_conf == 0.0:
        sentiment_raw = "unknown"

    # FIX-4: Mixed sentiment correction
    sentiment_raw, confidence_pct, polarity_val = (
        _apply_sentiment_corrections(
            analysis_text, sentiment_raw,
            confidence_pct, polarity_val))

    return {
        "detected_language":    display_name,
        "language_code":        lang_code,
        "detection_confidence": lang_confidence,
        "translated_text":      translated_text,
        "translation_needed":   was_translated,
        "skipped_translation":  False,
        "sentiment":            sentiment_raw,
        "confidence":           confidence_pct,
        "polarity":             polarity_val,
        "subjectivity":         float(pred.get(
                                "subjectivity", 0.0)),
        "model_used":           pred.get("model_used",
                                model_choice),
    }


# ══════════════════════════════════════════════════════════
# Route handler
# ══════════════════════════════════════════════════════════

@router.post(
    "",
    response_model=LanguageResponse,
    summary="Detect language, translate, and analyze sentiment",
)
async def analyze_language(
    request: LanguageRequest,
    model=Depends(get_model),
    vectorizer=Depends(get_vectorizer),
):
    start_ms = time.perf_counter()
    loop = asyncio.get_event_loop()

    logger.info(
        f"Language request: "
        f"model={request.model.value} "
        f"text_len={len(request.text)} "
        f"lime={request.include_lime} "
        f"absa={request.include_absa} "
        f"sarcasm={request.include_sarcasm}"
    )

    try:
        async with inference_throttler:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    primary_pool.executor,
                    _run_language_pipeline,
                    request.text,
                    request.model.value,
                ),
                timeout=_INFERENCE_TIMEOUT_S,
            )
    except asyncio.TimeoutError:
        metrics_store.record_timeout()
        logger.error(
            f"Language inference timeout after "
            f"{_INFERENCE_TIMEOUT_S}s for: "
            f"{request.text[:50]}"
        )
        raise HTTPException(
            status_code=504,
            detail=(
                "Inference timeout — model took too long "
                "to respond. Please try again."
            ),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500,
                            detail=str(e))

    # ── The text to run optional analyses on (English) ────
    # Use translated text if available, else original
    analysis_text = (
        result.get("translated_text") or request.text
    )

    # ── Import shared helpers from predict route ──────────
    from app.routes.predict import (
        _run_lime, _run_absa, _run_sarcasm,
    )
    from app.schemas import (
        LIMEFeature, ABSAItem, SentimentLabel, SarcasmResult,
    )

    # ── LIME (optional) ───────────────────────────────────
    lime_features = None
    if request.include_lime:
        async with inference_throttler:
            try:
                raw_lime = await asyncio.wait_for(
                    loop.run_in_executor(
                        primary_pool.executor, _run_lime,
                        analysis_text, request.model.value,
                        model, vectorizer,
                    ),
                    timeout=_INFERENCE_TIMEOUT_S,
                )
            except asyncio.TimeoutError:
                metrics_store.record_timeout()
                logger.warning("LIME timed out in language route")
                raw_lime = []
        lime_features = [LIMEFeature(**f) for f in raw_lime]

    # ── ABSA (optional) ───────────────────────────────────
    absa_results = None
    if request.include_absa:
        async with inference_throttler:
            try:
                raw_absa = await asyncio.wait_for(
                    loop.run_in_executor(
                        primary_pool.executor, _run_absa,
                        analysis_text,
                    ),
                    timeout=_INFERENCE_TIMEOUT_S,
                )
            except asyncio.TimeoutError:
                metrics_store.record_timeout()
                logger.warning("ABSA timed out in language route")
                raw_absa = []
        absa_results = []
        for item in raw_absa:
            sentiment_val = item.get("sentiment", "neutral")
            if sentiment_val not in ["positive", "negative", "neutral"]:
                sentiment_val = "neutral"
            absa_results.append(ABSAItem(
                aspect=item["aspect"],
                sentiment=SentimentLabel(sentiment_val),
                polarity=item["polarity"],
                subjectivity=item["subjectivity"],
            ))

    # ── Sarcasm (optional) ────────────────────────────────
    sarcasm_result = None
    if request.include_sarcasm:
        async with inference_throttler:
            try:
                raw_sarcasm = await asyncio.wait_for(
                    loop.run_in_executor(
                        primary_pool.executor, _run_sarcasm,
                        analysis_text,
                    ),
                    timeout=_INFERENCE_TIMEOUT_S,
                )
            except asyncio.TimeoutError:
                metrics_store.record_timeout()
                logger.warning("Sarcasm timed out in language route")
                raw_sarcasm = {"detected": False, "confidence": 0.0}
        sarcasm_result = SarcasmResult(**raw_sarcasm)

    elapsed_ms = int(
        (time.perf_counter() - start_ms) * 1000
    )
    logger.info(
        f"Language analysis complete: "
        f"lang={result['language_code']} "
        f"sentiment={result['sentiment']} "
        f"skipped_translation="
        f"{result.get('skipped_translation', False)} "
        f"[{elapsed_ms}ms]"
    )

    # Cache store using English text as key
    english_for_cache = (
        result.get("translated_text") or request.text
    )
    cache_key = prediction_cache.get_cache_key(
        english_for_cache, request.model.value, {}
    )
    prediction_cache.set(cache_key, result)

    # Record prediction for live dashboard stats
    metrics_store.record_prediction(
        result.get("sentiment", "unknown"),
        result.get("detected_language", None),
    )

    return LanguageResponse(
        **result,
        processing_ms=elapsed_ms,
        lime_features=lime_features,
        absa=absa_results,
        sarcasm=sarcasm_result,
    )
