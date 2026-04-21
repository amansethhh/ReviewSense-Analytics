"""
Centralized output contract enforcement for ReviewSense Analytics.

ADD-ON 1: Uncertain prediction enforcement — LAST step before output.
ADD-ON 2: Global output formatter — consistent fields everywhere.
ADD-ON 3: Translation fallback metrics tracking.

This module is the SINGLE SOURCE OF TRUTH for:
  - Confidence threshold
  - Uncertain label assignment
  - Output field standardization
"""

import logging
import threading
from typing import Any, Optional

logger = logging.getLogger("reviewsense.contract")

# ── Confidence threshold (on 0-100 scale) ─────────────────
# V3: This is metadata ONLY — it NEVER overrides the label.
# Only 3 labels allowed: positive, negative, neutral.
CONFIDENCE_THRESHOLD: float = 65.0


# ── ADD-ON 3: Translation fallback counter ─────────────────
_fallback_lock = threading.Lock()
_translation_stats = {
    "total_translations": 0,
    "fallback_count": 0,
    "validation_failures": 0,
}


def record_translation_fallback() -> None:
    """Thread-safe increment of translation fallback counter."""
    with _fallback_lock:
        _translation_stats["fallback_count"] += 1


def record_translation_attempt() -> None:
    """Thread-safe increment of total translation counter."""
    with _fallback_lock:
        _translation_stats["total_translations"] += 1


def record_translation_validation_failure() -> None:
    """Thread-safe increment of validation failure counter."""
    with _fallback_lock:
        _translation_stats["validation_failures"] += 1


def get_translation_stats() -> dict:
    """Return snapshot of translation metrics."""
    with _fallback_lock:
        total = _translation_stats["total_translations"]
        fallbacks = _translation_stats["fallback_count"]
        failures = _translation_stats["validation_failures"]
    return {
        "total_translations": total,
        "fallback_count": fallbacks,
        "validation_failures": failures,
        "fallback_rate": (
            round(fallbacks / total, 4) if total > 0 else 0.0
        ),
        "validation_failure_rate": (
            round(failures / total, 4) if total > 0 else 0.0
        ),
    }


# ── ADD-ON 1: Centralized uncertain enforcement ───────────

def enforce_uncertainty(
    sentiment: str,
    confidence: float,
    raw_label: Optional[str] = None,
) -> tuple[str, str, bool]:
    """
    V3: UNCERTAIN label REMOVED per user requirement.

    Only three valid output labels: positive, negative, neutral.
    The confidence value IS the uncertainty signal — it is displayed
    in the UI. A low-confidence neutral review is shown as "neutral"
    with low confidence, NOT as "uncertain".

    is_uncertain is kept as a metadata flag for API compatibility
    but NEVER overrides the label.

    Args:
        sentiment: The corrected sentiment label.
        confidence: Confidence percentage (0-100).
        raw_label: Original model label before any overrides.

    Returns:
        (final_label, raw_label, is_uncertain)
    """
    if raw_label is None:
        raw_label = sentiment

    is_uncertain = confidence < CONFIDENCE_THRESHOLD

    # V3: Label passes through unchanged — NEVER set to "uncertain"
    final_label = sentiment

    if is_uncertain:
        logger.debug(
            "Low confidence prediction (kept as %s): "
            "raw=%s conf=%.1f%% (threshold=%.1f%%)",
            final_label, raw_label, confidence,
            CONFIDENCE_THRESHOLD,
        )

    return final_label, raw_label, is_uncertain


# ── ADD-ON 2: Global output formatter ─────────────────────

def format_prediction_output(
    *,
    sentiment: str,
    confidence: float,
    polarity: float = 0.0,
    subjectivity: float = 0.0,
    analysis_input_source: str = "original",
    translation: str = "",
    translation_failed: bool = False,
    sarcasm_detected: bool = False,
    sarcasm_applied: bool = False,
    **extra: Any,
) -> dict:
    """
    Standardize prediction output with uncertain enforcement.

    This is the MANDATORY final step before returning any
    prediction result. Ensures ALL routes return identical
    field structures.

    Pipeline order enforced:
      Input → Detection → Translation → Validation
      → Inference → Sarcasm → Uncertain → THIS FORMATTER

    Args:
        sentiment: Post-correction sentiment label.
        confidence: Confidence percentage (0-100).
        polarity: Polarity score (-1.0 to 1.0).
        subjectivity: Subjectivity score (0.0 to 1.0).
        analysis_input_source: "original" | "translated" |
                               "original_fallback"
        sarcasm_detected: Whether sarcasm was detected.
        sarcasm_applied: Whether sarcasm flipped the label.
        **extra: Additional fields passed through unchanged.

    Returns:
        Standardized output dict with all contract fields.
    """
    # Enforce uncertainty as the LAST step
    final_label, raw_label, is_uncertain = enforce_uncertainty(
        sentiment, confidence,
        raw_label=extra.pop("raw_label", None),
    )

    output = {
        # Core contract fields (V3)
        "label": final_label,
        "confidence": confidence,
        "raw_label": raw_label,
        "is_uncertain": is_uncertain,
        "analysis_input_source": analysis_input_source,
        "translation": translation,
        "translation_failed": translation_failed,
        "sarcasm_detected": sarcasm_detected,
        "sarcasm_applied": sarcasm_applied,
        # Standard fields
        "polarity": polarity,
        "subjectivity": subjectivity,
    }

    # Pass through any extra fields (model_used, etc.)
    output.update(extra)

    return output


def format_bulk_row_output(
    *,
    sentiment: str,
    confidence: float,
    polarity: float = 0.0,
    subjectivity: float = 0.0,
    analysis_input_source: str = "original",
    translation: str = "",
    translation_failed: bool = False,
    sarcasm_detected: Optional[bool] = None,
    **extra: Any,
) -> dict:
    """
    Standardize bulk row output with uncertain enforcement.
    Lighter version for bulk pipeline (no sarcasm_applied tracking).
    """
    final_label, raw_label, is_uncertain = enforce_uncertainty(
        sentiment, confidence,
        raw_label=extra.pop("raw_label", None),
    )

    output = {
        "sentiment": final_label,
        "label": final_label,
        "confidence": confidence,
        "raw_label": raw_label,
        "is_uncertain": is_uncertain,
        "analysis_input_source": analysis_input_source,
        "translation": translation,
        "translation_failed": translation_failed,
        "sarcasm_detected": sarcasm_detected,
        "polarity": polarity,
        "subjectivity": subjectivity,
    }

    output.update(extra)

    return output
