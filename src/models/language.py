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
    "ja": "Japanese", "ko": "Korean", "ca": "Catalan", "nl": "Dutch",
    "sv": "Swedish", "no": "Norwegian", "da": "Danish", "fi": "Finnish",
    "pl": "Polish", "tr": "Turkish", "th": "Thai", "vi": "Vietnamese",
    "id": "Indonesian", "ms": "Malay", "ro": "Romanian", "cs": "Czech",
    "unknown": "Unknown",
}

LANGUAGE_FLAGS = {
    "en": "🇬🇧", "hi": "🇮🇳", "mr": "🇮🇳", "ta": "🇮🇳", "te": "🇮🇳",
    "bn": "🇮🇳", "gu": "🇮🇳", "pa": "🇮🇳", "ur": "🇵🇰", "es": "🇪🇸",
    "fr": "🇫🇷", "de": "🇩🇪", "it": "🇮🇹", "pt": "🇵🇹", "ru": "🇷🇺",
    "ar": "🇸🇦", "zh-cn": "🇨🇳", "zh-tw": "🇹🇼", "ja": "🇯🇵", "ko": "🇰🇷",
    "ca": "🇪🇸", "nl": "🇳🇱", "sv": "🇸🇪", "no": "🇳🇴", "da": "🇩🇰",
    "fi": "🇫🇮", "pl": "🇵🇱", "tr": "🇹🇷", "th": "🇹🇭", "vi": "🇻🇳",
    "id": "🇮🇩", "ms": "🇲🇾", "ro": "🇷🇴", "cs": "🇨🇿",
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
