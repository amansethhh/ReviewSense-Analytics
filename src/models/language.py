"""Language detection module — enhanced with Hinglish + Unicode script analysis.

Detection hierarchy (Problem 3 + ADD-ON 3):
  1. Hinglish pre-check (code-switched Roman Hindi/English)
  2. Unicode script analysis (non-Latin scripts: Cyrillic, Arabic, CJK, etc.)
  3. langdetect with confidence thresholding
  4. Fallback to English
"""

from __future__ import annotations

import logging

from langdetect import DetectorFactory, LangDetectException, detect_langs

logger = logging.getLogger("reviewsense")

DetectorFactory.seed = 42

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "mr": "Marathi", "ta": "Tamil",
    "te": "Telugu", "bn": "Bengali", "gu": "Gujarati", "pa": "Punjabi",
    "ur": "Urdu", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ar": "Arabic",
    "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
    "zh": "Chinese", "ja": "Japanese", "ko": "Korean", "ca": "Catalan",
    "nl": "Dutch", "sv": "Swedish", "no": "Norwegian", "da": "Danish",
    "fi": "Finnish", "pl": "Polish", "tr": "Turkish", "th": "Thai",
    "vi": "Vietnamese", "id": "Indonesian", "ms": "Malay", "ro": "Romanian",
    "cs": "Czech",
    "unknown": "Unknown",
}

LANGUAGE_FLAGS = {
    "en": "🇬🇧", "hi": "🇮🇳", "mr": "🇮🇳", "ta": "🇮🇳", "te": "🇮🇳",
    "bn": "🇮🇳", "gu": "🇮🇳", "pa": "🇮🇳", "ur": "🇵🇰", "es": "🇪🇸",
    "fr": "🇫🇷", "de": "🇩🇪", "it": "🇮🇹", "pt": "🇵🇹", "ru": "🇷🇺",
    "ar": "🇸🇦", "zh-cn": "🇨🇳", "zh-tw": "🇹🇼", "zh": "🇨🇳",
    "ja": "🇯🇵", "ko": "🇰🇷",
    "ca": "🇪🇸", "nl": "🇳🇱", "sv": "🇸🇪", "no": "🇳🇴", "da": "🇩🇰",
    "fi": "🇫🇮", "pl": "🇵🇱", "tr": "🇹🇷", "th": "🇹🇭", "vi": "🇻🇳",
    "id": "🇮🇩", "ms": "🇲🇾", "ro": "🇷🇴", "cs": "🇨🇿",
}


# ═══════════════════════════════════════════════════════════════
# ADD-ON 3 — Unicode script ranges for non-Latin detection
# ═══════════════════════════════════════════════════════════════

CYRILLIC_RANGE   = range(0x0400, 0x04FF)
ARABIC_RANGE     = range(0x0600, 0x06FF)
CJK_RANGE        = range(0x4E00, 0x9FFF)
HANGUL_RANGE     = range(0xAC00, 0xD7AF)
DEVANAGARI_RANGE = range(0x0900, 0x097F)


def detect_script(text: str) -> str | None:
    """Unicode block analysis for non-Latin script detection.

    Returns ISO language code if non-Latin script detected, else None.
    Unicode detection takes priority over all other methods.
    """
    for char in text:
        cp = ord(char)
        if cp in CYRILLIC_RANGE:
            return "ru"
        if cp in ARABIC_RANGE:
            return "ar"
        if cp in CJK_RANGE:
            return "zh"
        if cp in HANGUL_RANGE:
            return "ko"
        if cp in DEVANAGARI_RANGE:
            return "hi"
    return None


# ═══════════════════════════════════════════════════════════════
# Problem 3 — Hinglish / code-switched detection
# ═══════════════════════════════════════════════════════════════

HINGLISH_MARKERS = {
    "accha", "acha", "bahut", "hai", "nahi", "nahin", "kya", "mujhe",
    "bilkul", "sundar", "bura", "zyada", "thoda", "theek", "tik",
    "pasand", "khareed", "paisa", "achha", "bekaar", "bekar",
    "sahi", "galat", "dukaan", "khana", "ganda", "mast",
    "yaar", "bhai", "ekdum", "aur", "lekin", "matlab", "wala",
    "wali", "wale", "phir", "abhi", "bohot", "seedha",
}


def detect_hinglish(text: str) -> bool:
    """Detect Hinglish (code-switched Hindi-English in Roman script).

    Uses curated Hindi word markers. Returns True if 2+ markers found.
    """
    tokens = set(text.lower().split())
    overlap = tokens & HINGLISH_MARKERS
    return len(overlap) >= 2


# ═══════════════════════════════════════════════════════════════
# ADD-ON 3 — langdetect with confidence thresholding
# ═══════════════════════════════════════════════════════════════

def detect_language_with_confidence(text: str) -> tuple:
    """Run langdetect and return (lang_code, probability)."""
    try:
        results = detect_langs(text)
        top = results[0]
        return str(top.lang), float(top.prob)
    except Exception:
        return "en", 0.0


# ═══════════════════════════════════════════════════════════════
# MAIN — detect_language_safe() + detect_language()
# ═══════════════════════════════════════════════════════════════

def detect_language_safe(text: str) -> str:
    """Full language detection hierarchy (replaces bare langdetect.detect).

    Priority order:
      1. Hinglish pre-check (code-switched Roman Hindi)
      2. Unicode script analysis (non-Latin scripts — highest confidence)
      3. langdetect with confidence thresholding
      4. Fallback to English
    """
    text = str(text or "").strip()
    if not text:
        return "en"

    # Tier 1: Hinglish
    if detect_hinglish(text):
        logger.info("Hinglish detected in: '%s...'", text[:50])
        return "hi"

    # Tier 2: Unicode block (non-Latin scripts always identifiable)
    script_lang = detect_script(text)
    if script_lang:
        logger.debug("Unicode script detected: %s", script_lang)
        return script_lang

    # Tier 3: langdetect with confidence threshold
    lang, prob = detect_language_with_confidence(text)
    if prob < 0.85:
        # Low confidence — double the text for more signal then retry
        lang2, prob2 = detect_language_with_confidence(text + " " + text)
        if prob2 > prob:
            return lang2

    return lang if lang else "en"


def detect_language(text: str) -> dict:
    """Detect language of input text using enhanced detection hierarchy.

    Returns: {"code", "name", "flag_emoji", "hinglish_detected"}
    """
    text = str(text or "").strip()
    if not text:
        return {"code": "unknown", "name": "Unknown", "flag_emoji": "🏳️",
                "hinglish_detected": False}

    # Check Hinglish first (for the flag)
    is_hinglish = detect_hinglish(text)

    # Use full detection hierarchy
    code = detect_language_safe(text)

    return {
        "code": code,
        "name": LANGUAGE_NAMES.get(code, code.title()),
        "flag_emoji": LANGUAGE_FLAGS.get(code, "🏳️"),
        "hinglish_detected": is_hinglish,
    }
