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

import re

# Fast regex patterns for each script (replaces char-by-char iteration)
_RE_HIRAGANA   = re.compile(r'[\u3040-\u309f]')
_RE_KATAKANA   = re.compile(r'[\u30a0-\u30ff]')
_RE_HANGUL     = re.compile(r'[\uac00-\ud7af]')
_RE_CJK        = re.compile(r'[\u4e00-\u9fff]')
_RE_ARABIC     = re.compile(r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]')
_RE_CYRILLIC   = re.compile(r'[\u0400-\u04ff]')
_RE_DEVANAGARI = re.compile(r'[\u0900-\u097f]')
_RE_BENGALI    = re.compile(r'[\u0980-\u09ff]')
_RE_TAMIL      = re.compile(r'[\u0b80-\u0bff]')
_RE_THAI       = re.compile(r'[\u0e00-\u0e7f]')

_SCRIPT_THRESHOLD = 0.15  # min ratio of script chars to trigger detection

# V4 FIX 3: Common English sentiment words that appear in short reviews.
# Used to guard against langdetect misrouting short English texts.
_ENGLISH_SHORT_PATTERN = re.compile(
    r'\b(worst|best|terrible|awful|amazing|great|good|bad|poor|excellent|'
    r'perfect|horrible|fantastic|outstanding|dreadful|useless|broken|'
    r'love|loved|hate|hated|nice|fine|okay|ok|mediocre|average|decent|'
    r'highly recommend|do not recommend|waste of money|value for money|'
    r'five stars|one star|two stars|three stars|four stars|'
    r'not worth|worth|quality|product|service|delivery|'
    r'disappointed|disappointing|satisfied|satisfying|'
    r'returned|refund|cheap|expensive|overpriced)\b',
    re.IGNORECASE
)


def detect_script(text: str) -> str | None:
    """Unicode block analysis for non-Latin script detection.

    Returns ISO language code if non-Latin script detected, else None.
    Unicode detection takes priority over all other methods.

    BUG-2 FIX: Japanese kana (Hiragana/Katakana) is checked BEFORE CJK
    to prevent misclassifying Japanese text as Chinese.
    Uses fast regex instead of slow char-by-char iteration.
    """
    if not text:
        return None

    total = max(len(text), 1)

    # CRITICAL: Japanese kana BEFORE Chinese CJK
    kana = len(_RE_HIRAGANA.findall(text)) + len(_RE_KATAKANA.findall(text))
    if kana > 0:  # ANY kana = Japanese
        return "ja"

    if len(_RE_HANGUL.findall(text)) / total > _SCRIPT_THRESHOLD:
        return "ko"
    if len(_RE_CJK.findall(text)) / total > _SCRIPT_THRESHOLD:
        return "zh"
    if len(_RE_ARABIC.findall(text)) / total > _SCRIPT_THRESHOLD:
        return "ar"
    if len(_RE_CYRILLIC.findall(text)) / total > _SCRIPT_THRESHOLD:
        return "ru"
    if len(_RE_DEVANAGARI.findall(text)) / total > _SCRIPT_THRESHOLD:
        return "hi"
    if len(_RE_BENGALI.findall(text)) / total > _SCRIPT_THRESHOLD:
        return "bn"
    if len(_RE_TAMIL.findall(text)) / total > _SCRIPT_THRESHOLD:
        return "ta"
    if len(_RE_THAI.findall(text)) / total > _SCRIPT_THRESHOLD:
        return "th"

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
      0. Short-text ASCII English guard (< 8 words, predominantly ASCII)
      1. Unicode script analysis (non-Latin scripts — highest confidence, fastest)
      2. Hinglish pre-check (code-switched Roman Hindi)
      3. langdetect with confidence thresholding
      4. Fallback to English

    V4 FIX 3: Added Tier 0 to prevent short English phrases from being
    misdetected and routed to XLM-R (which gives ~44% confidence for English).
    """
    text = str(text or "").strip()
    if not text:
        return "en"

    words = text.split()

    # Tier 0: Short-text ASCII English guard (V4 FIX 3)
    # Statistical detectors fail on < 8 words of ASCII text.
    # If text is predominantly ASCII, it cannot be CJK/Arabic/Hindi etc.
    if len(words) <= 8:
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        ascii_ratio = ascii_chars / max(len(text), 1)
        if ascii_ratio > 0.80:
            # Check for common English vocabulary
            if _ENGLISH_SHORT_PATTERN.search(text):
                logger.debug(
                    "[LANG] Short-text English guard: matched vocab in '%s'", text[:50]
                )
                return "en"
            # Pure ASCII short text → English default
            # (Chinese/Japanese/Korean/Arabic/Hindi would never be ASCII)
            if all(ord(c) < 128 for c in text.replace(' ', '')):
                logger.debug(
                    "[LANG] Short-text ASCII guard: pure ASCII '%s' → en", text[:50]
                )
                return "en"

    # Tier 1: Unicode block (non-Latin scripts always identifiable)
    script_lang = detect_script(text)
    if script_lang:
        logger.debug("Unicode script detected: %s", script_lang)
        return script_lang

    # Tier 2: Hinglish (only on Latin-script text, so safe after Unicode check)
    if detect_hinglish(text):
        logger.info("Hinglish detected in: '%s...'", text[:50])
        return "hi"

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
