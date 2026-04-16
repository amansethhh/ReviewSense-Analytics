"""
Shared utility functions for the ReviewSense backend.

O5: Confidence normalization guard — makes the 0-1 → 0-100
transformation explicit, testable, and impossible to skip.
"""

import logging

logger = logging.getLogger("reviewsense.utils")


def normalize_confidence(raw: float) -> float:
    """
    Convert a raw confidence score from the ML model's
    [0.0, 1.0] range to the API's [0.0, 100.0] percentage.

    Args:
        raw: Confidence score from src.predict.predict_sentiment().
             Must be in [0.0, 1.0] range.

    Returns:
        Confidence as a percentage, rounded to 2 decimal places.

    Raises:
        ValueError: If raw is outside the valid [0.0, 1.0] range
                    (with a tiny epsilon buffer for floating-point
                    precision).
    """
    raw = float(raw)

    # Allow tiny epsilon above 1.0 for floating-point precision
    if raw < 0.0 or raw > 1.0 + 1e-6:
        raise ValueError(
            f"Confidence must be in [0.0, 1.0], got {raw}"
        )

    # Clamp to exact [0.0, 1.0] after epsilon check
    raw = max(0.0, min(1.0, raw))

    return round(raw * 100, 2)
