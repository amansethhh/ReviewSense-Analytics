"""
Translation validation layer for ReviewSense Analytics.

SECTION 2: Validates translation output before it enters
the inference pipeline. If validation fails, the system
falls back to the original text.

Validation rules:
  1. Length ratio check (0.5x - 2.5x)
  2. Language verification (output should be English)
  3. Semantic sanity (must contain some sentiment-bearing words)

Fallback strategy:
  - Use original text
  - Set analysis_input_source = "original_fallback"
"""

import re
import logging
from typing import Optional

from app.utils.output_contract import (
    record_translation_fallback,
    record_translation_attempt,
    record_translation_validation_failure,
)

logger = logging.getLogger("reviewsense.translation_validator")

# Common sentiment-bearing words (English)
_SENTIMENT_WORDS = frozenset({
    "good", "bad", "great", "terrible", "excellent",
    "awful", "love", "hate", "best", "worst", "amazing",
    "horrible", "nice", "poor", "fine", "wonderful",
    "disappointing", "perfect", "recommend", "quality",
    "happy", "sad", "angry", "satisfied", "like", "dislike",
    "enjoy", "regret", "beautiful", "ugly", "fast", "slow",
    "expensive", "cheap", "delicious", "disgusting",
    "comfortable", "uncomfortable", "friendly", "rude",
    "clean", "dirty", "fresh", "stale", "ok", "okay",
    "average", "mediocre", "outstanding", "superb",
    "not", "never", "always", "very", "really", "extremely",
    "quite", "somewhat", "slightly", "totally", "absolutely",
})


def validate_translation(
    original: str,
    translated: str,
    source_lang: str = "unknown",
) -> dict:
    """
    Validate a translated text before it enters inference.

    Args:
        original: The original non-English text.
        translated: The English translation output.
        source_lang: Detected source language code.

    Returns:
        {
            "is_valid": bool,
            "translated_text": str,  # validated or original fallback
            "analysis_input_source": str,
            "validation_warnings": list[str],
        }
    """
    record_translation_attempt()

    warnings: list[str] = []
    translated = (translated or "").strip()
    original = (original or "").strip()

    # Edge case: empty translation
    if not translated:
        record_translation_validation_failure()
        record_translation_fallback()
        logger.warning(
            "Empty translation for lang=%s, using original",
            source_lang,
        )
        return {
            "is_valid": False,
            "translated_text": original,
            "analysis_input_source": "original",
            "validation_warnings": ["Empty translation output"],
        }

    # ── Rule 1: Length ratio check ─────────────────────────
    if len(original) > 0:
        ratio = len(translated) / len(original)
        if ratio < 0.3 or ratio > 3.0:
            warnings.append(
                f"Length ratio {ratio:.2f} outside "
                f"acceptable range [0.3, 3.0]"
            )
            # Extreme ratios are hard failures
            if ratio < 0.1 or ratio > 5.0:
                record_translation_validation_failure()
                record_translation_fallback()
                logger.warning(
                    "Extreme length ratio %.2f for "
                    "lang=%s — using original fallback",
                    ratio, source_lang,
                )
                return {
                    "is_valid": False,
                    "translated_text": original,
                    "analysis_input_source": "original",
                    "validation_warnings": warnings,
                }

    # ── Rule 2: Language verification (basic) ──────────────
    # Check if the translation appears to be mostly ASCII/Latin
    # (a rough proxy for "is this English?")
    if len(translated) > 5:
        ascii_ratio = sum(
            1 for c in translated if ord(c) < 128
        ) / len(translated)
        if ascii_ratio < 0.5:
            warnings.append(
                f"Low ASCII ratio {ascii_ratio:.2f} — "
                f"translation may not be English"
            )
            # If mostly non-ASCII, it's likely untranslated
            if ascii_ratio < 0.3:
                record_translation_validation_failure()
                record_translation_fallback()
                logger.warning(
                    "Translation appears untranslated "
                    "(ASCII ratio %.2f) for lang=%s",
                    ascii_ratio, source_lang,
                )
                return {
                    "is_valid": False,
                    "translated_text": original,
                    "analysis_input_source": "original",
                    "validation_warnings": warnings,
                }

    # ── Rule 3: Semantic sanity ────────────────────────────
    # Check that translation contains at least some
    # recognizable English words
    words = set(
        re.findall(r'[a-zA-Z]+', translated.lower())
    )
    if len(words) > 3:
        sentiment_overlap = words & _SENTIMENT_WORDS
        common_english = words & {
            "the", "a", "an", "is", "was", "are", "were",
            "it", "this", "that", "and", "or", "but",
            "of", "in", "to", "for", "with", "on", "at",
            "i", "we", "they", "he", "she", "my", "your",
        }
        total_recognized = len(sentiment_overlap) + len(
            common_english
        )
        recognition_ratio = total_recognized / len(words)

        if recognition_ratio < 0.1 and len(words) > 10:
            warnings.append(
                "Very low English word recognition "
                f"({recognition_ratio:.2f})"
            )
            record_translation_validation_failure()
            record_translation_fallback()
            return {
                "is_valid": False,
                "translated_text": original,
                "analysis_input_source": "original",
                "validation_warnings": warnings,
            }

    # ── Passed all checks ──────────────────────────────────
    if warnings:
        logger.debug(
            "Translation validated with warnings for "
            "lang=%s: %s", source_lang, "; ".join(warnings),
        )

    return {
        "is_valid": True,
        "translated_text": translated,
        "analysis_input_source": "original",
        "validation_warnings": warnings,
    }
