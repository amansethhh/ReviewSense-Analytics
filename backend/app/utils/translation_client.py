"""
Translation client — NLLB-only (V4 architecture).

V4: Single translation engine. No fallbacks, no retries to
external services. NLLB runs locally.

If NLLB fails → return original text with status "failed".
Translation is for DISPLAY ONLY — never affects sentiment.
"""

import logging
from typing import Tuple

logger = logging.getLogger("reviewsense.translation_client")


def translate_with_retry(
    text: str,
    source_lang: str,
    target_lang: str = "en",
    timeout: float = 10.0,
) -> Tuple[str, str]:
    """
    Translate text using NLLB (local model).

    V4: No external API calls. No retries needed since NLLB
    runs locally. If it fails, return original text.

    Returns:
        Tuple of (translated_text, status)
        status: "success" | "failed"
    """
    try:
        from src.models.translation import translate_to_english

        translated, method = translate_to_english(text, source_lang)

        if method in ("nllb", "cache", "passthrough"):
            return (translated, "success")
        else:
            # passthrough_failed
            return (text, "failed")

    except Exception as e:
        logger.error(
            "[NLLB] Translation error for lang=%s: %s",
            source_lang, e,
        )
        return (text, "failed")
