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
            _nllb_tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                use_fast=False,
            )
            if not hasattr(_nllb_tokenizer, "lang_code_to_id"):
                _nllb_tokenizer.lang_code_to_id = {
                    "eng_Latn": _nllb_tokenizer.convert_tokens_to_ids("eng_Latn")
                }
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

LANG_MAP = {
    "hi": "hin_Deva",
    "ar": "arb_Arab",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "es": "spa_Latn",
    "it": "ita_Latn",
    "pt": "por_Latn",
    "ja": "jpn_Jpan",
    "zh": "zho_Hans",
}

_NLLB_LANG_MAP = {
    **LANG_MAP,
    "en": "eng_Latn",
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
    "he": "heb_Hebr",
    "bn": "ben_Beng",
    "ta": "tam_Taml",
    "ur": "urd_Arab",
    "fa": "pes_Arab",
    "zh-cn": "zho_Hans",
    "zh-tw": "zho_Hant",
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


def _get_nllb_code(iso_code: str) -> str | None:
    """Convert ISO 639-1 code to NLLB flores200 code."""
    code = str(iso_code or "").strip().lower()
    if code.startswith("zh"):
        code = "zh" if code not in ("zh-tw", "zh-hant") else "zh-tw"
    return _NLLB_LANG_MAP.get(code)


def _english_bos_token_id() -> int:
    """Return the required NLLB English BOS token id."""
    return _nllb_tokenizer.lang_code_to_id["eng_Latn"]


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

# V4 FIX 4: Patterns for template/fallback strings that are NOT real NLLB output
_TEMPLATE_PATTERN = re.compile(
    r'\[(Hindi|Arabic|Chinese|Japanese|Korean|Russian|German|French|'
    r'Spanish|Italian|Portuguese|Polish|Turkish|Vietnamese|Indonesian|'
    r'Thai|Hebrew|Ukrainian|Bulgarian|Greek|Persian|Bengali|HI|AR|ZH|'
    r'JA|KO|RU|DE|FR|ES|IT|PT|PL|Translated)\]',
    re.IGNORECASE
)

_GENERIC_TEMPLATE = re.compile(
    r'^The (product|quality|item|service) is (great|good|bad|poor|excellent|'
    r'terrible|decent|acceptable|outstanding|fantastic|mediocre|'
    r'unsatisfactory|average|very (good|bad|poor))[\.\!]?'
    r'(\s*\[.*\])?$',
    re.IGNORECASE
)

_MIN_LENGTH_RATIO = 0.25


def _is_degenerate(original: str, translated: str) -> bool:
    """Return True if translation is unusable."""
    if not translated or not translated.strip():
        return True

    t = translated.strip()
    t_lower = t.lower()

    if t_lower in _DEGENERATE_STRINGS:
        return True

    # V4 FIX 4: Check for template/fallback strings
    if _TEMPLATE_PATTERN.search(t):
        return True
    if _GENERIC_TEMPLATE.match(t):
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


def is_bad_translation(original: str, translated: str) -> bool:
    """V4 FIX 4: Public API to check if translation is template/fallback.

    Returns True if the translation is a template, degenerate, or empty.
    Used by validation tests and downstream consumers.
    """
    if not translated or not translated.strip():
        return True
    t = translated.strip()
    if _TEMPLATE_PATTERN.search(t):
        return True
    if _GENERIC_TEMPLATE.match(t):
        return True
    return _is_degenerate(original, t)


def validate_translation(text: str, translated: str) -> bool:
    """Validate translated display text before exposing it."""
    source = str(text or "").strip()
    candidate = str(translated or "").strip()
    if len(candidate) < 3:
        return False
    if candidate == source:
        return False
    if "[" in candidate:
        return False
    if _is_degenerate(source, candidate):
        return False
    return True


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
        if src_nllb is None:
            logger.warning("[NLLB] Unsupported source language: %s", src_lang_code)
            return None
        _nllb_tokenizer.src_lang = src_nllb

        inputs = _nllb_tokenizer(
            [text],
            return_tensors="pt",
            padding=True,
            max_length=512,
            truncation=True,
        )

        tokens = _nllb_model.generate(
            **inputs,
            forced_bos_token_id=_english_bos_token_id(),
            max_length=256,
        )

        return _nllb_tokenizer.batch_decode(
            tokens, skip_special_tokens=True
        )[0]

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

    if result and validate_translation(text, result):
        cleaned = result.strip()

        if cleaned and validate_translation(text, cleaned):
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
    if src_nllb is None:
        logger.warning("[NLLB] Unsupported batch source language: %s", src_lang)
        return texts
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

        outputs = _nllb_model.generate(
            **inputs,
            forced_bos_token_id=_english_bos_token_id(),
            max_length=256,
        )

        translated = _nllb_tokenizer.batch_decode(
            outputs, skip_special_tokens=True
        )

        translated_iter = iter([tr.strip() for tr in translated])
        results = []
        for text in texts:
            t = str(text or "")
            if t.strip():
                tr = next(translated_iter)
                if not validate_translation(t, tr):
                    results.append(t)
                else:
                    results.append(tr)
            else:
                results.append(t)
        return results

    except Exception as e:
        logger.warning("[NLLB] Batch translation failed for %s: %s", src_lang, e)
        return texts
