"""Language detection and translation helpers for ReviewSense Analytics."""

from __future__ import annotations

from functools import lru_cache

from langdetect import DetectorFactory, LangDetectException, detect

DetectorFactory.seed = 42

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "ur": "Urdu",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ar": "Arabic",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ja": "Japanese",
    "ko": "Korean",
    "unknown": "Unknown",
}

LANGUAGE_FLAGS = {
    "en": "🇬🇧",
    "hi": "🇮🇳",
    "mr": "🇮🇳",
    "ta": "🇮🇳",
    "te": "🇮🇳",
    "bn": "🇮🇳",
    "gu": "🇮🇳",
    "pa": "🇮🇳",
    "ur": "🇵🇰",
    "es": "🇪🇸",
    "fr": "🇫🇷",
    "de": "🇩🇪",
    "it": "🇮🇹",
    "pt": "🇵🇹",
    "ru": "🇷🇺",
    "ar": "🇸🇦",
    "zh-cn": "🇨🇳",
    "zh-tw": "🇹🇼",
    "ja": "🇯🇵",
    "ko": "🇰🇷",
}


@lru_cache(maxsize=1)
def _get_translator():
    try:
        from googletrans import Translator
    except Exception:
        return None

    try:
        return Translator()
    except Exception:
        return None


def _language_name(language_code: str) -> str:
    return LANGUAGE_NAMES.get(language_code, language_code.title())


def _language_flag(language_code: str) -> str:
    return LANGUAGE_FLAGS.get(language_code, "🏳️")


def detect_and_translate(text):
    """Detect language and translate non-English text to English."""

    original_text = str(text or "").strip()
    if not original_text:
        return {
            "original_text": "",
            "translated_text": "",
            "detected_language": "unknown",
            "language_name": "Unknown",
            "was_translated": False,
            "flag_emoji": "🏳️",
        }

    try:
        detected_language = detect(original_text)
    except LangDetectException:
        detected_language = "unknown"

    translated_text = original_text
    was_translated = False

    if detected_language not in {"en", "unknown"}:
        try:
            translator = _get_translator()
            if translator is None:
                raise RuntimeError("Translation backend is unavailable.")

            translated_text = translator.translate(
                original_text,
                src=detected_language,
                dest="en",
            ).text
            was_translated = translated_text.strip() != original_text
        except Exception:
            translated_text = original_text
            was_translated = False

    return {
        "original_text": original_text,
        "translated_text": translated_text,
        "detected_language": detected_language,
        "language_name": _language_name(detected_language),
        "was_translated": was_translated,
        "flag_emoji": _language_flag(detected_language),
    }
