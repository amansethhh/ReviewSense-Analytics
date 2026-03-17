"""Language detection module — uses langdetect."""

from __future__ import annotations

from langdetect import DetectorFactory, LangDetectException, detect

DetectorFactory.seed = 42

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "mr": "Marathi", "ta": "Tamil",
    "te": "Telugu", "bn": "Bengali", "gu": "Gujarati", "pa": "Punjabi",
    "ur": "Urdu", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ar": "Arabic",
    "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
    "ja": "Japanese", "ko": "Korean", "unknown": "Unknown",
}

LANGUAGE_FLAGS = {
    "en": "🇬🇧", "hi": "🇮🇳", "mr": "🇮🇳", "ta": "🇮🇳", "te": "🇮🇳",
    "bn": "🇮🇳", "gu": "🇮🇳", "pa": "🇮🇳", "ur": "🇵🇰", "es": "🇪🇸",
    "fr": "🇫🇷", "de": "🇩🇪", "it": "🇮🇹", "pt": "🇵🇹", "ru": "🇷🇺",
    "ar": "🇸🇦", "zh-cn": "🇨🇳", "zh-tw": "🇹🇼", "ja": "🇯🇵", "ko": "🇰🇷",
}


def detect_language(text: str) -> dict:
    """Detect language of input text.

    Returns: {"code", "name", "flag_emoji"}
    """
    text = str(text or "").strip()
    if not text:
        return {"code": "unknown", "name": "Unknown", "flag_emoji": "🏳️"}

    try:
        code = detect(text)
    except LangDetectException:
        code = "unknown"

    return {
        "code": code,
        "name": LANGUAGE_NAMES.get(code, code.title()),
        "flag_emoji": LANGUAGE_FLAGS.get(code, "🏳️"),
    }
