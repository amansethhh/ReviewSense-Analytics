"""Translation module — deep-translator (Google) with degenerate output detection.

Replaces the previous googletrans + Helsinki-NLP implementation.

Architecture:
  Tier 1: deep-translator GoogleTranslator (reliable, maintained)
  Tier 2: Passthrough with failure flag

Translation cache: in-process dict (survives Streamlit reruns, up to 500 entries).
Degenerate output detection: pattern matching + length ratio guard.
"""

from __future__ import annotations

import hashlib
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Optional, Tuple

logger = logging.getLogger("reviewsense.translation")

# ═══════════════════════════════════════════════════════════════
# Circuit breaker — fast-fail when deep_translator is missing
# ═══════════════════════════════════════════════════════════════

_DEEP_TRANSLATOR_AVAILABLE: bool
try:
    import deep_translator as _dt_check  # noqa: F401
    _DEEP_TRANSLATOR_AVAILABLE = True
    logger.info("[INIT] deep_translator: AVAILABLE")
except ImportError:
    _DEEP_TRANSLATOR_AVAILABLE = False
    logger.error(
        "[INIT] deep_translator NOT INSTALLED — translation disabled. "
        "Run: pip install deep-translator==1.11.4"
    )

# ═══════════════════════════════════════════════════════════════
# Translation memory cache
# ═══════════════════════════════════════════════════════════════

_translation_cache: dict = {}
_cache_lock = threading.Lock()
_MAX_CACHE_SIZE = 500

# Dedicated executor for Google translate calls (avoids blocking event loop)
_translate_executor = ThreadPoolExecutor(
    max_workers=3, thread_name_prefix="src_translate"
)

# ═══════════════════════════════════════════════════════════════
# Degenerate output detection
# ═══════════════════════════════════════════════════════════════

# Patterns that indicate a broken/template translation
_DEGENERATE_PATTERNS = [
    re.compile(r"^\s*$"),                                                    # empty
    re.compile(r"^\[.+\]$"),                                                  # just a lang tag
    re.compile(r"\[(Chinese|Japanese|Korean|Arabic|Hindi|Russian|German|French|Spanish|Polish|Portuguese|Italian)\]", re.IGNORECASE),  # leaked lang tag
    re.compile(r"^(Bad experience|Good experience|It does not work properly)\.$", re.IGNORECASE),
    re.compile(r"^(This product is (bad|good|okay))\.$", re.IGNORECASE),
    re.compile(r"^(The quality is (decent|mediocre|acceptable))\.$", re.IGNORECASE),
]

# Minimum translation length ratio vs source text (words)
_MIN_LENGTH_RATIO = 0.35

# Known passthrough strings (Helsinki garbage outputs)
_DEGENERATE_STRINGS = frozenset({
    "...", "…", ".", "..", "—", "--",
    "the", "a", "i", "it", "is", "yes", "no", "ok", "okay",
    "null", "none", "undefined", "bad experience", "error",
    "translation error",
})


def _is_degenerate(original: str, translated: str) -> bool:
    """Return True if translation is unusable."""
    if not translated or not translated.strip():
        return True

    t = translated.strip()
    t_lower = t.lower()

    # Known bad strings
    if t_lower in _DEGENERATE_STRINGS:
        return True

    # Pattern matches
    for pat in _DEGENERATE_PATTERNS:
        if pat.search(t):
            return True

    # Length ratio — translation should be proportional to source
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
# Language code normalization
# ═══════════════════════════════════════════════════════════════

# deep-translator expects specific codes for some languages
_LANG_CODE_MAP = {
    "zh-cn": "zh-CN",
    "zh-tw": "zh-TW",
    "zh":    "zh-CN",
    "pt":    "pt",
    "he":    "iw",      # Google uses 'iw' for Hebrew
}


def _normalize_lang_code(code: str) -> str:
    """Normalize ISO code to deep-translator/Google format."""
    code = str(code or "").strip().lower()
    return _LANG_CODE_MAP.get(code, code)


# ═══════════════════════════════════════════════════════════════
# Core translation function
# ═══════════════════════════════════════════════════════════════

_GOOGLE_TIMEOUT_S = 4.0   # reduced from 5.0 — fail faster


def _google_translate_sync(text: str, source_code: str) -> Optional[str]:
    """Run GoogleTranslator in an executor thread with timeout.

    CIRCUIT BREAKER: Returns None immediately if deep_translator is
    not installed — prevents 5s hang per review.
    """
    # Fast-fail if package unavailable (circuit breaker)
    if not _DEEP_TRANSLATOR_AVAILABLE:
        return None

    try:
        from deep_translator import GoogleTranslator

        future = _translate_executor.submit(
            lambda: GoogleTranslator(source=source_code, target="en").translate(text)
        )
        result = future.result(timeout=_GOOGLE_TIMEOUT_S)
        return result
    except FuturesTimeoutError:
        logger.warning("Google translate timeout (%.1fs) for lang=%s", _GOOGLE_TIMEOUT_S, source_code)
        return None
    except Exception as e:
        logger.warning("Google translate error for lang=%s: %s", source_code, e)
        return None


def translate_to_english(
    text: str,
    src_lang: str = "auto",
) -> str:
    """
    Translate `text` from `src_lang` to English.

    Uses deep-translator GoogleTranslator with:
    - Degenerate output detection
    - In-process translation cache (500 entries)
    - 5-second per-call timeout

    Returns:
        Translated English text, or original text if translation fails.
    """
    text = str(text or "").strip()
    if not text:
        return ""

    # English passthrough
    src_norm = _normalize_lang_code(src_lang)
    if src_lang.lower() in ("en", "english") or src_norm == "en":
        return text

    # Cache lookup
    cache_key = hashlib.md5(f"{src_lang}:{text}".encode()).hexdigest()
    with _cache_lock:
        if cache_key in _translation_cache:
            return _translation_cache[cache_key]

    # Translate
    result = _google_translate_sync(text, src_norm if src_norm != "en" else "auto")

    if result and not _is_degenerate(text, result):
        cleaned = result.strip()
        # Strip leaked language-name suffixes
        cleaned = re.sub(
            r'\s*[,.]?\s*(?:Hindi|Chinese|Korean|Arabic|Russian|German|French|'
            r'Spanish|Italian|Portuguese|Japanese|Thai|Turkish|Swedish|Dutch|'
            r'Polish|Bengali|Tamil)\s*[.]?\s*$',
            '', cleaned, flags=re.IGNORECASE
        ).strip()

        with _cache_lock:
            if len(_translation_cache) >= _MAX_CACHE_SIZE:
                # Evict oldest 100 entries
                keys = list(_translation_cache.keys())[:100]
                for k in keys:
                    del _translation_cache[k]
            _translation_cache[cache_key] = cleaned

        logger.debug("Translated [%s→en]: '%s...' → '%s...'",
                     src_lang, text[:40], cleaned[:40])
        return cleaned

    # Translation failed or degenerate — return original
    logger.warning("Translation failed/degenerate for lang=%s: '%s' → '%s'",
                   src_lang, text[:50], str(result)[:50] if result else "None")
    return text


# ═══════════════════════════════════════════════════════════════
# Backward compatibility shim for src/translator.py callers
# ═══════════════════════════════════════════════════════════════

def _load_helsinki_model():
    """Stub — Helsinki model removed. Returns (None, None) for compat."""
    return None, None
