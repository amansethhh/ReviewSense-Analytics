"""Translation module — NLLB (Meta) single engine.

V4 ARCHITECTURE:
  - ONLY engine: facebook/nllb-200-distilled-600M
  - Translation is for DISPLAY ONLY — never affects sentiment
  - On failure: return original text with translation_failed=True
  - No fallback engines, no templates, no Helsinki, no Google

Translation cache: in-process dict (up to 500 entries).
Degenerate output detection: pattern matching + length ratio guard.
"""

from __future__ import annotations

import hashlib
import logging
import re
import threading
from typing import Optional, Tuple

logger = logging.getLogger("reviewsense.translation")

# ═══════════════════════════════════════════════════════════════
# NLLB Model — lazy-loaded singleton
# ═══════════════════════════════════════════════════════════════

_nllb_lock = threading.Lock()
_nllb_model = None
_nllb_tokenizer = None
_nllb_available: bool | None = None  # None = untested


def _load_nllb():
    """Lazy-load NLLB model + tokenizer. Thread-safe singleton."""
    global _nllb_model, _nllb_tokenizer, _nllb_available
    with _nllb_lock:
        if _nllb_available is not None:
            return _nllb_available
        try:
            from transformers import (
                AutoTokenizer,
                AutoModelForSeq2SeqLM,
            )
            model_name = "facebook/nllb-200-distilled-600M"
            logger.info("[NLLB] Loading model: %s", model_name)
            _nllb_tokenizer = AutoTokenizer.from_pretrained(model_name)
            _nllb_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            _nllb_available = True
            logger.info("[NLLB] Model loaded successfully")
        except Exception as e:
            _nllb_available = False
            logger.error(
                "[NLLB] Failed to load model: %s. "
                "Translation will return original text.",
                e,
            )
        return _nllb_available


# ═══════════════════════════════════════════════════════════════
# NLLB language code mapping
# ISO 639-1 → NLLB flores200 codes
# ═══════════════════════════════════════════════════════════════

_NLLB_LANG_MAP = {
    "en": "eng_Latn",
    "es": "spa_Latn",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "it": "ita_Latn",
    "pt": "por_Latn",
    "nl": "nld_Latn",
    "pl": "pol_Latn",
    "sv": "swe_Latn",
    "da": "dan_Latn",
    "no": "nob_Latn",
    "fi": "fin_Latn",
    "ro": "ron_Latn",
    "hu": "hun_Latn",
    "cs": "ces_Latn",
    "sk": "slk_Latn",
    "hr": "hrv_Latn",
    "bg": "bul_Cyrl",
    "sr": "srp_Cyrl",
    "sl": "slv_Latn",
    "tr": "tur_Latn",
    "ru": "rus_Cyrl",
    "uk": "ukr_Cyrl",
    "el": "ell_Grek",
    "ar": "arb_Arab",
    "he": "heb_Hebr",
    "hi": "hin_Deva",
    "bn": "ben_Beng",
    "ta": "tam_Taml",
    "ur": "urd_Arab",
    "fa": "pes_Arab",
    "zh": "zho_Hans",
    "zh-cn": "zho_Hans",
    "zh-tw": "zho_Hant",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "th": "tha_Thai",
    "vi": "vie_Latn",
    "id": "ind_Latn",
    "ms": "zsm_Latn",
    "tl": "tgl_Latn",
    "sw": "swh_Latn",
    "ka": "kat_Geor",
    "ca": "cat_Latn",
    "lv": "lvs_Latn",
    "lt": "lit_Latn",
    "et": "est_Latn",
}


def _get_nllb_code(iso_code: str) -> str:
    """Convert ISO 639-1 code to NLLB flores200 code."""
    code = str(iso_code or "").strip().lower()
    return _NLLB_LANG_MAP.get(code, "eng_Latn")


# ═══════════════════════════════════════════════════════════════
# Translation cache
# ═══════════════════════════════════════════════════════════════

_translation_cache: dict = {}
_cache_lock = threading.Lock()
_MAX_CACHE_SIZE = 500


# ═══════════════════════════════════════════════════════════════
# Degenerate output detection
# ═══════════════════════════════════════════════════════════════

_DEGENERATE_PATTERNS = [
    re.compile(r"^\s*$"),
    re.compile(r"^\[.+\]$"),
    re.compile(r"^\.{1,3}$"),
]

_DEGENERATE_STRINGS = frozenset({
    "...", "…", ".", "..", "—", "--",
    "the", "a", "i", "it", "is", "yes", "no", "ok", "okay",
    "null", "none", "undefined", "error",
    "translation error",
})

_MIN_LENGTH_RATIO = 0.25


def _is_degenerate(original: str, translated: str) -> bool:
    """Return True if translation is unusable."""
    if not translated or not translated.strip():
        return True

    t = translated.strip()
    t_lower = t.lower()

    if t_lower in _DEGENERATE_STRINGS:
        return True

    for pat in _DEGENERATE_PATTERNS:
        if pat.search(t):
            return True

    # Length ratio check
    src_words = len(original.split())
    tr_words = len(t.split())
    if src_words >= 6 and tr_words < src_words * _MIN_LENGTH_RATIO:
        return True

    # Single repeated token
    tokens = t_lower.split()
    if len(tokens) >= 3 and len(set(tokens)) == 1:
        return True

    return False


# ═══════════════════════════════════════════════════════════════
# Core NLLB translation function
# ═══════════════════════════════════════════════════════════════

def _translate_nllb(
    text: str,
    src_lang_code: str,
    tgt_lang: str = "eng_Latn",
) -> Optional[str]:
    """Translate text using NLLB model.

    Returns translated text or None on failure.
    """
    if not _load_nllb():
        return None

    try:
        # Set source language for tokenizer
        src_nllb = _get_nllb_code(src_lang_code)
        _nllb_tokenizer.src_lang = src_nllb

        inputs = _nllb_tokenizer(
            text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
        )

        # Get target language token ID
        tgt_token_id = _nllb_tokenizer.convert_tokens_to_ids(tgt_lang)

        tokens = _nllb_model.generate(
            **inputs,
            forced_bos_token_id=tgt_token_id,
            max_length=512,
        )

        result = _nllb_tokenizer.decode(
            tokens[0], skip_special_tokens=True
        )
        return result

    except Exception as e:
        logger.warning(
            "[NLLB] Translation failed for lang=%s: %s",
            src_lang_code, e,
        )
        return None


# ═══════════════════════════════════════════════════════════════
# Public API — translate_to_english
# ═══════════════════════════════════════════════════════════════

def translate_to_english(
    text: str,
    src_lang: str = "auto",
) -> tuple:
    """
    Translate `text` from `src_lang` to English using NLLB.

    V4 CONTRACT:
      On success: (English translation, "nllb")
      On English passthrough: (original_text, "passthrough")
      On cache hit: (cached_translation, "cache")
      On failure: (original_text, "passthrough_failed")

    NLLB is the ONLY translation engine. No fallbacks.
    Translation is for DISPLAY ONLY — never affects sentiment.

    Returns:
        Tuple of (translated_text, method)
    """
    text = str(text or "").strip()
    if not text:
        return "", "passthrough"

    # English passthrough
    src_norm = str(src_lang or "").strip().lower()
    if src_norm in ("en", "english", "eng_latn"):
        return text, "passthrough"

    # Cache lookup
    cache_key = hashlib.md5(
        f"{src_lang}:{text}".encode()
    ).hexdigest()
    with _cache_lock:
        if cache_key in _translation_cache:
            return _translation_cache[cache_key], "cache"

    # Translate with NLLB
    result = _translate_nllb(text, src_norm)

    if result and not _is_degenerate(text, result):
        cleaned = result.strip()

        if cleaned and not _is_degenerate(text, cleaned):
            # Cache the result
            with _cache_lock:
                if len(_translation_cache) >= _MAX_CACHE_SIZE:
                    keys = list(_translation_cache.keys())[:100]
                    for k in keys:
                        del _translation_cache[k]
                _translation_cache[cache_key] = cleaned

            logger.debug(
                "[NLLB] Translated [%s→en]: '%s...' → '%s...'",
                src_lang, text[:40], cleaned[:40],
            )
            return cleaned, "nllb"

    # Translation failed — return original with failure flag
    src_norm_display = src_norm if src_norm else "unknown"
    logger.warning(
        "Translation failed for lang=%s: output='%s'",
        src_norm_display,
        str(result)[:50] if result else "None",
    )
    return text, "passthrough_failed"


# ═══════════════════════════════════════════════════════════════
# Batch translation
# ═══════════════════════════════════════════════════════════════

def translate_batch(
    texts: list[str],
    src_lang: str,
) -> list[str]:
    """Translate a batch of texts from src_lang to English.

    V4: Uses NLLB batch inference with batch_decode for high throughput.
    """
    if not _load_nllb():
        return texts  # Fallback to original

    src_nllb = _get_nllb_code(src_lang)
    _nllb_tokenizer.src_lang = src_nllb

    # Filter out empty texts
    valid_texts = [t for t in texts if str(t or "").strip()]
    if not valid_texts:
        return texts

    try:
        inputs = _nllb_tokenizer(
            valid_texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )

        tgt_token_id = _nllb_tokenizer.convert_tokens_to_ids("eng_Latn")

        outputs = _nllb_model.generate(
            **inputs,
            forced_bos_token_id=tgt_token_id,
            max_length=512,
        )

        translated = _nllb_tokenizer.batch_decode(
            outputs, skip_special_tokens=True
        )

        # Merge back with original preserving empty strings
        result_map = {t: tr.strip() for t, tr in zip(valid_texts, translated)}
        results = []
        for text in texts:
            t = str(text or "")
            if t.strip():
                tr = result_map[t]
                if _is_degenerate(t, tr):
                    results.append(t)
                else:
                    results.append(tr)
            else:
                results.append(t)
        return results

    except Exception as e:
        logger.warning("[NLLB] Batch translation failed for %s: %s", src_lang, e)
        return texts
