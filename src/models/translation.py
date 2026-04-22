"""Translation module — NLLB (Meta) single engine.

V5 ARCHITECTURE:
  - ONLY engine: facebook/nllb-200-distilled-600M
  - Translation is USED for inference ONLY when validated.
    If translation passes trust check → RoBERTa on translated text.
    If translation fails trust check → fallback to XLM-R on original.
  - On failure: return original text with translation_failed=True
  - No fallback engines, no templates, no Helsinki, no Google

Translation cache: in-process dict (up to 500 entries).
Degenerate output detection: pattern matching + length ratio guard.
Section 2: Semantic guard rejects polarity-inverted translations.
Section 4: Hinglish normalizer converts common Hinglish to English.
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
    """V4+Section 1: Public API to check if translation is template/fallback.

    Returns True if the translation is a template, degenerate, empty,
    or suspiciously generic.
    """
    if not translated or not translated.strip():
        return True
    t = translated.strip()

    # Too short to be a real translation
    if len(t.split()) < 3:
        return True

    # Template bracket tags
    if "[" in t or "]" in t:
        return True

    if _TEMPLATE_PATTERN.search(t):
        return True
    if _GENERIC_TEMPLATE.match(t):
        return True

    # Section 1: Additional generic patterns that indicate hallucination
    _generic_phrases = [
        "this product is", "the quality is", "this service is",
        "the product is", "this item is", "the item is",
    ]
    t_lower = t.lower()
    for phrase in _generic_phrases:
        if t_lower.startswith(phrase):
            return True

    return _is_degenerate(original, t)


# ═══════════════════════════════════════════════════════════════
# Section 2 — Semantic polarity guard
# ═══════════════════════════════════════════════════════════════

# Keywords indicating source text polarity (language-agnostic common patterns)
_NEGATIVE_SOURCE_KEYWORDS = frozenset({
    "खराब", "बेकार", "गंदा", "बुरा", "नही", "worst", "terrible",
    "horrible", "awful", "disgusting", "سيء", "فظيع", "mauvais",
    "horrible", "schlecht", "furchtbar", "最悪", "ひどい", "糟糕",
    "bakwaas", "bakwas", "kharab", "wahiyat", "bekar", "ganda",
})

_POSITIVE_TRANSLATION_SIGNALS = frozenset({
    "excellent", "great", "amazing", "wonderful", "fantastic",
    "outstanding", "superb", "best", "love", "perfect",
    "highly recommend", "very good",
})

_NEGATIVE_TRANSLATION_SIGNALS = frozenset({
    "terrible", "horrible", "awful", "worst", "disgusting",
    "waste", "bad", "poor", "useless", "hate", "never buy",
})


def _has_negative_source_keywords(text: str) -> bool:
    """Check if source text contains strong negative sentiment keywords."""
    t_lower = text.lower()
    return any(kw in t_lower for kw in _NEGATIVE_SOURCE_KEYWORDS)


def semantic_guard_check(source: str, translated: str) -> bool:
    """Section 2: Detect polarity inversion between source and translation.

    Returns True if the translation appears to INVERT the sentiment
    of the source text (e.g., negative source → positive translation).
    This is a lightweight heuristic, NOT a model call.
    """
    t_lower = translated.lower()

    # Check: negative source keywords → positive translation
    if _has_negative_source_keywords(source):
        if any(sig in t_lower for sig in _POSITIVE_TRANSLATION_SIGNALS):
            logger.warning(
                "Semantic guard: negative source but positive translation detected"
            )
            return True  # Inversion detected

    return False


# ═══════════════════════════════════════════════════════════════
# Section 4 — Hinglish normalizer (lightweight)
# ═══════════════════════════════════════════════════════════════

_HINGLISH_REPLACEMENTS = {
    "bakwaas": "very bad",
    "bakwas": "very bad",
    "zabardast": "excellent",
    "acha": "good",
    "accha": "good",
    "achha": "good",
    "kharab": "bad",
    "bekar": "useless",
    "bekaar": "useless",
    "paisa vasool": "worth the money",
    "paisa barbaad": "waste of money",
    "wahiyat": "terrible",
    "mast": "awesome",
    "ganda": "dirty",
    "lajawab": "outstanding",
    "dhansu": "superb",
    "kamaal": "wonderful",
    "mazaa": "fun",
    "maza": "fun",
    "bhot": "very",
    "bohot": "very",
    "bahut": "very",
    "nahi": "not",
    "bilkul": "absolutely",
    "ekdum": "totally",
    "pasand": "liked",
    "sundar": "beautiful",
    "bura": "bad",
    "theek": "okay",
    "tik": "okay",
    "zyada": "more",
    "thoda": "little",
    # V5 additions: common social media Hinglish
    "faltu": "useless",
    "dhokha": "fraud",
    "barbaad": "wasted",
    "pagal": "crazy",
    "behtareen": "excellent",
    "shandar": "magnificent",
    "ghatiya": "poor quality",
    "badiya": "great",
}

# Hindi filler words that should be stripped (not translated)
_HINGLISH_FILLERS = frozenset({
    "yeh", "ye", "hai", "hain", "ho", "tha", "thi", "the",
    "ka", "ki", "ke", "ko", "me", "mein", "se", "pe", "par",
    "bhi", "toh", "to", "na", "woh", "wo", "koi", "kuch",
    "yaar", "bhai", "arre", "aur", "lekin", "matlab",
    "wala", "wali", "wale", "phir", "abhi",
})


def normalize_hinglish(text: str) -> str:
    """Section 4: Convert common Hinglish slang to English equivalents.

    Applied ONLY when is_hinglish() returns True (checked by caller).
    Steps:
      1. Replace known Hinglish words with English equivalents
      2. Strip leftover Hindi filler words that confuse RoBERTa
      3. Clean up whitespace
    """
    result = text.lower()

    # Step 1: Multi-word phrases first (order matters)
    for hindi_word, english_word in _HINGLISH_REPLACEMENTS.items():
        if " " in hindi_word:
            result = result.replace(hindi_word, english_word)

    # Step 2: Single-word replacements
    words = result.split()
    normalized = []
    for word in words:
        # Strip punctuation for lookup
        clean = word.strip(".,!?;:")
        punct = word[len(clean):] if len(clean) < len(word) else ""

        if clean in _HINGLISH_REPLACEMENTS:
            normalized.append(_HINGLISH_REPLACEMENTS[clean] + punct)
        elif clean in _HINGLISH_FILLERS:
            continue  # Drop filler words
        else:
            normalized.append(word)

    result = " ".join(normalized)
    # Clean up double spaces
    while "  " in result:
        result = result.replace("  ", " ")
    return result.strip()


def validate_translation(text: str, translated: str) -> bool:
    """Validate translated display text before exposing it.

    Section 2: Now includes semantic polarity guard.
    """
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
    # Section 2: Reject polarity-inverted translations
    if semantic_guard_check(source, candidate):
        logger.warning(
            "Translation rejected by semantic guard: '%s' → '%s'",
            source[:40], candidate[:40],
        )
        return False
    return True


# ═══════════════════════════════════════════════════════════════
# Section 3 — Translation trust gate
# ═══════════════════════════════════════════════════════════════

def has_sentiment_keywords(text: str) -> tuple:
    """Section 3: Detect sentiment keyword signals in text.

    Returns (has_positive, has_negative) tuple.
    """
    positives = ["good", "excellent", "amazing", "great", "wonderful",
                 "fantastic", "superb", "love", "perfect", "best"]
    negatives = ["bad", "terrible", "worst", "poor", "horrible",
                 "awful", "disgusting", "waste", "useless", "hate"]

    t = text.lower()
    pos = any(p in t for p in positives)
    neg = any(n in t for n in negatives)
    return pos, neg


def translation_trust_check(original: str, translated: str) -> tuple:
    """Section 3: Full translation trust validation.

    Returns (trusted: bool, reason: str) where reason explains rejection.
    Combines format, polarity, and length checks.
    """
    # Format check
    if is_bad_translation(original, translated):
        return False, "bad_format"

    # Polarity mismatch detection
    orig_pos, orig_neg = has_sentiment_keywords(original)
    trans_pos, trans_neg = has_sentiment_keywords(translated)

    if orig_neg and trans_pos and not trans_neg:
        logger.warning(
            "[TRUST GATE] Polarity inversion: negative source → positive translation"
        )
        return False, "polarity_inversion"

    if orig_pos and trans_neg and not trans_pos:
        logger.warning(
            "[TRUST GATE] Polarity inversion: positive source → negative translation"
        )
        return False, "polarity_inversion"

    # Length sanity (V5: tightened to 0.5–2.0 for stricter validation)
    orig_words = max(len(original.split()), 1)
    trans_words = len(translated.split())
    ratio = trans_words / orig_words

    if ratio < 0.5 or ratio > 2.0:
        logger.warning(
            "[TRUST GATE] Length ratio %.2f outside bounds [0.5, 2.0]",
            ratio,
        )
        return False, "length_mismatch"

    # V5 FIX 4: Reject if translation is identical to source (no actual translation)
    if translated.strip().lower() == original.strip().lower():
        return False, "identical_to_source"

    return True, "trusted"


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

    V5 CONTRACT:
      On success: (English translation, "nllb")
      On English passthrough: (original_text, "passthrough")
      On cache hit: (cached_translation, "cache")
      On failure: (original_text, "passthrough_failed")

    NLLB is the ONLY translation engine. No fallbacks.
    Translation is used for inference when validated;
    fallback to XLM-R on original text when translation fails.

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
