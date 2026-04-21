"""
V3 Prediction Output Validator — Safety middleware.

Catches any route deviation from the three-class output contract:
  - Only "positive", "negative", "neutral" are valid labels
  - "uncertain" is NEVER a valid output label (V3 mandate)
  - Confidence must be 0–100
  - Polarity must be -1.0 to 1.0
  - Subjectivity must be 0.0 to 1.0

Usage:
    from app.utils.validator import validate_prediction_output
    result = validate_prediction_output(result_dict)
"""

import logging

logger = logging.getLogger("reviewsense.validator")

# Three-class output contract — the ONLY valid labels
VALID_LABELS = frozenset({"positive", "negative", "neutral"})

# Labels that must NEVER appear in V3 output
FORBIDDEN_LABELS = frozenset({"uncertain", "unknown", "error"})


def validate_prediction_output(result: dict) -> dict:
    """Validate and sanitize a prediction output dict.

    Ensures the three-class output contract is enforced.
    Invalid labels are corrected to "neutral" with a log warning.

    Args:
        result: Prediction output dict with at least "sentiment" key.

    Returns:
        Sanitized result dict (mutated in place for performance).
    """
    if not isinstance(result, dict):
        logger.error("validate_prediction_output received non-dict: %s", type(result))
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "polarity": 0.0,
            "subjectivity": 0.5,
        }

    # ── Label enforcement ─────────────────────────────────
    sentiment = result.get("sentiment", "neutral")
    if isinstance(sentiment, str):
        sentiment = sentiment.lower().strip()

    if sentiment in FORBIDDEN_LABELS:
        logger.warning(
            "V3 VIOLATION: Forbidden label '%s' detected — "
            "correcting to 'neutral'. Confidence=%.1f",
            sentiment,
            result.get("confidence", 0.0),
        )
        result["sentiment"] = "neutral"
    elif sentiment not in VALID_LABELS:
        logger.warning(
            "V3 VIOLATION: Unknown label '%s' detected — "
            "correcting to 'neutral'",
            sentiment,
        )
        result["sentiment"] = "neutral"
    else:
        result["sentiment"] = sentiment

    # ── Confidence bounds ─────────────────────────────────
    confidence = result.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    result["confidence"] = max(0.0, min(100.0, confidence))

    # ── Polarity bounds ───────────────────────────────────
    polarity = result.get("polarity", 0.0)
    try:
        polarity = float(polarity)
    except (TypeError, ValueError):
        polarity = 0.0
    result["polarity"] = max(-1.0, min(1.0, polarity))

    # ── Subjectivity bounds ───────────────────────────────
    subjectivity = result.get("subjectivity", 0.5)
    try:
        subjectivity = float(subjectivity)
    except (TypeError, ValueError):
        subjectivity = 0.5
    result["subjectivity"] = max(0.0, min(1.0, subjectivity))

    return result


def validate_bulk_results(results: list[dict]) -> list[dict]:
    """Validate a list of bulk prediction results.

    Applies validate_prediction_output to each row.
    Returns the sanitized list.
    """
    if not results:
        return results

    violations = 0
    for result in results:
        original_label = result.get("sentiment", "")
        validate_prediction_output(result)
        if result["sentiment"] != original_label:
            violations += 1

    if violations > 0:
        logger.warning(
            "V3 Bulk validation: %d/%d results had label violations "
            "(corrected to three-class contract)",
            violations, len(results),
        )

    return results
