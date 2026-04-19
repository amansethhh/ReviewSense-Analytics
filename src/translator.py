"""Language detection and translation — backward-compatible wrapper.

Delegates to src.models.language and src.models.translation.
Enhanced with Hinglish detection and translation quality signals.
"""

from __future__ import annotations

from src.models.language import LANGUAGE_NAMES, LANGUAGE_FLAGS


def detect_and_translate(text):
    """Detect language and translate non-English text to English.

    Uses Helsinki-NLP/opus-mt-mul-en for offline translation,
    with googletrans as fallback. Enhanced with Hinglish detection
    and translation quality validation.
    """
    from src.models.language import detect_language
    from src.models.translation import translate_to_english

    original_text = str(text or "").strip()
    if not original_text:
        return {
            "original_text": "",
            "translated_text": "",
            "detected_language": "unknown",
            "language_name": "Unknown",
            "was_translated": False,
            "flag_emoji": "🏳️",
            "hinglish_detected": False,
        }

    lang = detect_language(original_text)
    lang_code = lang["code"]
    hinglish_detected = lang.get("hinglish_detected", False)

    translated_text = original_text
    was_translated = False

    if hinglish_detected:
        # Skip translation for Hinglish — use direct inference
        pass
    elif lang_code not in ("en", "unknown"):
        translated_text = translate_to_english(original_text, src_lang=lang_code)
        was_translated = translated_text.strip().lower() != original_text.strip().lower()

    return {
        "original_text": original_text,
        "translated_text": translated_text,
        "detected_language": lang_code,
        "language_name": lang["name"],
        "was_translated": was_translated,
        "flag_emoji": lang["flag_emoji"],
        "hinglish_detected": hinglish_detected,
    }
