"""
Centralized 4-tier language detection system for ReviewSense Analytics.

BUG-2 FIX: Resolves CJK confusion (Japanese ≠ Chinese), Portuguese ≠ French.

Tier 1: Unicode script analysis (most accurate for CJK/Cyrillic/Arabic)
Tier 2: Hinglish (Hindi + English code-switching) detection
Tier 3: langdetect library (good for European languages)
Tier 4: Fallback to English

All routes (predict, language, bulk) import from here — single source of truth.
"""

from __future__ import annotations

import re
import logging
from typing import Optional

logger = logging.getLogger("reviewsense.language_detection")


# ═══════════════════════════════════════════════════════════════
# TIER 1 — Unicode script analysis
# ═══════════════════════════════════════════════════════════════

def detect_script_unicode(text: str) -> Optional[str]:
    """
    Detect language via Unicode character ranges.
    Most accurate for CJK scripts — resolves Japanese ≠ Chinese confusion.

    Priority order matters:
    1. Japanese (Hiragana/Katakana) — BEFORE Chinese CJK
    2. Korean (Hangul)
    3. Chinese (CJK Unified, only if no Japanese kana)
    4. Arabic, Cyrillic, Devanagari, Bengali, Tamil, Thai

    Returns ISO 639-1 language code or None if no script detected.
    """
    if not text or not text.strip():
        return None

    # Count characters in each script range
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    japanese_hiragana = len(re.findall(r'[\u3040-\u309f]', text))
    japanese_katakana = len(re.findall(r'[\u30a0-\u30ff]', text))
    korean_chars = len(re.findall(r'[\uac00-\ud7af]', text))
    arabic_chars = len(re.findall(
        r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff'
        r'\ufb50-\ufdff\ufe70-\ufeff]', text))
    cyrillic_chars = len(re.findall(r'[\u0400-\u04ff]', text))
    devanagari_chars = len(re.findall(r'[\u0900-\u097f]', text))
    bengali_chars = len(re.findall(r'[\u0980-\u09ff]', text))
    tamil_chars = len(re.findall(r'[\u0b80-\u0bff]', text))
    thai_chars = len(re.findall(r'[\u0e00-\u0e7f]', text))

    total_chars = max(len(text.strip()), 1)

    # ── CRITICAL: Japanese BEFORE Chinese ──────────────────
    # Japanese uses Hiragana/Katakana (unique to Japanese)
    # mixed with CJK characters (shared with Chinese).
    # If ANY Hiragana or Katakana is present → Japanese.
    japanese_kana = japanese_hiragana + japanese_katakana
    if japanese_kana > 0:
        logger.debug(
            "Japanese detected: %d hiragana + %d katakana "
            "(+ %d CJK shared chars)",
            japanese_hiragana, japanese_katakana, chinese_chars,
        )
        return "ja"

    # Korean (Hangul is unique to Korean)
    if korean_chars > total_chars * 0.2:
        return "ko"

    # Chinese (CJK Unified — only if NO Japanese kana)
    if chinese_chars > total_chars * 0.2:
        return "zh-cn"

    # Arabic (extended ranges)
    if arabic_chars > total_chars * 0.2:
        return "ar"

    # Russian/Cyrillic
    if cyrillic_chars > total_chars * 0.2:
        return "ru"

    # Hindi (Devanagari)
    if devanagari_chars > total_chars * 0.2:
        return "hi"

    # Bengali
    if bengali_chars > total_chars * 0.2:
        return "bn"

    # Tamil
    if tamil_chars > total_chars * 0.2:
        return "ta"

    # Thai
    if thai_chars > total_chars * 0.2:
        return "th"

    return None


# ═══════════════════════════════════════════════════════════════
# TIER 2 — Hinglish (Hindi + English) detection
# ═══════════════════════════════════════════════════════════════

HINGLISH_MARKERS = [
    "yaar", "bas", "kya", "hai", "hoon", "tha", "thi", "bhi",
    "nahi", "haan", "abhi", "wala", "waala", "achha", "accha",
    "thik", "theek", "matlab", "arre", "oye", "bhai", "dost",
    "bahut", "bohot", "kuch", "aur", "lekin", "magar",
    "kaafi", "sahi", "galat", "bakwas", "bekar", "mast",
]

_SHORT_ENGLISH_MARKERS = frozenset({
    "amazing", "awful", "bad", "best", "broken", "decent",
    "excellent", "fantastic", "good", "great", "horrible",
    "love", "loved", "neutral", "nice", "not", "okay", "poor",
    "service", "slow", "terrible", "worst",
})


def detect_hinglish(text: str) -> bool:
    """Detect Hinglish (Hindi + English code-switching).

    Returns True if text contains ≥2 Hinglish marker words.
    Also True if text mixes English ASCII with Devanagari script.
    """
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))
    marker_count = sum(1 for m in HINGLISH_MARKERS if m in words)

    # Script mixing: English ASCII + Devanagari
    has_english = bool(re.search(r'[a-zA-Z]', text))
    has_devanagari = bool(re.search(r'[\u0900-\u097f]', text))

    return (marker_count >= 2) or (has_english and has_devanagari)


# ═══════════════════════════════════════════════════════════════
# TIER 3 — langdetect library
# ═══════════════════════════════════════════════════════════════

# Polish diacritical characters for disambiguation
_POLISH_CHARS = set('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')

# Portuguese markers for pt/es disambiguation
_PORTUGUESE_MARKERS = re.compile(
    r'(?:ção|ções|ões|lho|lha|ão|ã|nh[ao]'
    r'|\bmuito\b|\bproduto\b|\bbom\b|\bnão\b'
    r'|\bótimo\b|\bpéssimo\b)',
    re.IGNORECASE,
)

# Supported language codes (whitelist)
_SUPPORTED_LANG_CODES = frozenset({
    "en", "hi", "ta", "bn", "es", "fr", "de",
    "zh-cn", "zh-tw", "ar", "pt", "ru", "ja",
    "ko", "it", "nl", "tr", "sv", "th", "pl",
})

# Language display names
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


def _langdetect_with_disambiguation(text: str) -> tuple[str, float]:
    """Tier 3: langdetect with Portuguese/Spanish disambiguation
    and Polish diacritics detection.

    Returns (language_code, confidence).
    """
    text_clean = text.strip()

    # Polish diacritics (before langdetect)
    if len(set(text_clean) & _POLISH_CHARS) >= 1:
        return ("pl", 1.0)

    # Adaptive threshold based on text length
    word_count = len(text_clean.split())
    if word_count <= 3:
        threshold = 0.70
    elif word_count <= 8:
        threshold = 0.85
    else:
        threshold = 0.92

    try:
        from langdetect import detect_langs, DetectorFactory
        DetectorFactory.seed = 42  # deterministic

        langs = detect_langs(text_clean)
        if not langs:
            return ("unknown", 0.0)

        top_lang = langs[0]

        # Portuguese/Spanish disambiguation
        if top_lang.lang == "es" and _PORTUGUESE_MARKERS.search(text_clean):
            logger.debug("Portuguese markers → overriding es → pt")
            return ("pt", max(top_lang.prob, 0.85))

        # Reject unsupported codes
        if top_lang.lang not in _SUPPORTED_LANG_CODES:
            if len(langs) > 1 and langs[1].lang in _SUPPORTED_LANG_CODES:
                return (langs[1].lang, langs[1].prob)
            return ("en", 0.0)

        # English confidence check
        if top_lang.lang == "en":
            ascii_ratio = sum(
                c.isascii() for c in text_clean
            ) / max(len(text_clean), 1)
            if ascii_ratio < 0.6:
                if len(langs) > 1:
                    return (langs[1].lang, langs[1].prob)
                return ("unknown", 0.0)
            if top_lang.prob >= threshold:
                return ("en", top_lang.prob)
            if len(langs) > 1 and langs[1].prob > 0.15:
                return (langs[1].lang, langs[1].prob)
            return ("en", top_lang.prob)
        else:
            return (top_lang.lang, top_lang.prob)

    except Exception as e:
        logger.warning("langdetect failed: %s", e)
        return ("unknown", 0.0)


# ═══════════════════════════════════════════════════════════════
# MAIN — 4-tier detection pipeline
# ═══════════════════════════════════════════════════════════════

def detect_language_robust(text: str) -> dict:
    """
    4-tier language detection system. Most accurate method wins.

    Returns dict with:
      language (str): ISO code
      language_name (str): display name
      confidence (float): 0.0–1.0
      method (str): which tier was used
      is_hinglish (bool): whether Hinglish detected
    """
    if not text or not text.strip():
        return {
            "language": "unknown",
            "language_name": "Unknown",
            "confidence": 0.0,
            "method": "empty",
            "is_hinglish": False,
        }

    text = text.strip()

    # Tier 1: Unicode script analysis (most accurate for CJK)
    unicode_lang = detect_script_unicode(text)
    if unicode_lang:
        is_hinglish = (
            detect_hinglish(text) if unicode_lang == "hi" else False
        )
        return {
            "language": unicode_lang,
            "language_name": LANGUAGE_CODE_MAP.get(
                unicode_lang, unicode_lang.title()),
            "confidence": 0.95,
            "method": "unicode_script",
            "is_hinglish": is_hinglish,
        }

    # Tier 2: Hinglish detection (Latin-script Hindi + English)
    if detect_hinglish(text):
        return {
            "language": "hi",
            "language_name": "Hindi (Hinglish)",
            "confidence": 0.90,
            "method": "hinglish_detection",
            "is_hinglish": True,
        }

    words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
    ascii_ratio = sum(c.isascii() for c in text) / max(len(text), 1)
    if ascii_ratio >= 0.95 and words & _SHORT_ENGLISH_MARKERS:
        return {
            "language": "en",
            "language_name": "English",
            "confidence": 0.95,
            "method": "english_lexical_guard",
            "is_hinglish": False,
        }

    # Tier 3: langdetect with disambiguation
    lang_code, lang_conf = _langdetect_with_disambiguation(text)
    if lang_code != "unknown":
        return {
            "language": lang_code,
            "language_name": LANGUAGE_CODE_MAP.get(
                lang_code, lang_code.title()),
            "confidence": lang_conf,
            "method": "langdetect",
            "is_hinglish": False,
        }

    # Tier 4: Fallback to English
    return {
        "language": "en",
        "language_name": "English",
        "confidence": 0.0,
        "method": "fallback",
        "is_hinglish": False,
    }


def is_confidently_english(text: str) -> bool:
    """Returns True only if highly confident the text is English."""
    result = detect_language_robust(text)
    return result["language"] == "en" and result["confidence"] >= 0.85
