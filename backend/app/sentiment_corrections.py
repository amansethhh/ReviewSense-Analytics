"""
Shared sentiment correction utilities.
Applied post-prediction in both /predict and /language routes.
Corrects known model weaknesses:
  - Double negatives: "not bad" -> NEUTRAL when model says NEGATIVE
  - Mixed "but" clauses: "good but expensive" -> NEUTRAL
  - Positive misclassification of mixed texts
"""
from __future__ import annotations

import re
import logging
from typing import Tuple

logger = logging.getLogger("reviewsense.corrections")

# Patterns that indicate a double-negative construction
_DOUBLE_NEG_PATTERNS = [
    r"\bnot\s+(bad|terrible|awful|horrible|poor|worse|worst|dreadful)\b",
    r"\bnot\s+too\s+(bad|terrible|awful)\b",
    r"\bnot\s+that\s+(bad|terrible|awful)\b",
    r"\bwasn[''t]+\s+(bad|terrible|awful)\b",
    r"\bisn[''t]+\s+(bad|terrible|awful)\b",
    r"\baren[''t]+\s+(bad|terrible|awful)\b",
    r"\bnot\s+\w+\s+at\s+all\b",
]

# Positive words
_POSITIVE_WORDS = frozenset([
    "good", "great", "excellent", "amazing", "fantastic",
    "wonderful", "outstanding", "brilliant", "superb",
    "perfect", "loved", "enjoyed", "liked", "appreciate",
    "nice", "fine", "decent",
])

# Negative words indicating a "but" contrast
_NEGATIVE_WORDS = frozenset([
    "expensive", "overpriced", "slow", "pricey", "costly",
    "bad", "poor", "disappointing", "horrible", "terrible",
    "awful", "frustrating", "annoying",
])

_DOUBLE_NEG_RE = [re.compile(p, re.IGNORECASE)
                  for p in _DOUBLE_NEG_PATTERNS]

# But-clause detection
_BUT_WORDS = re.compile(
    r"\b(but|however|although|though|yet)\b", re.IGNORECASE
)

# Confidence threshold below which "but" clause correction
# is applied (for sentiment == "negative")
_BUT_CLAUSE_CONF_THRESHOLD = 70.0


def apply_sentiment_corrections(
    text: str,
    sentiment: str,
    confidence: float,
) -> Tuple[str, float, bool]:
    """
    Apply post-prediction corrections to the raw model output.

    Returns:
        (corrected_sentiment, corrected_confidence, was_corrected)

    Rules:
    1. Double negative + (NEGATIVE or low-conf POSITIVE) ->
       correct to NEUTRAL
    2. Positive+but clause + NEGATIVE sentiment +
       confidence < 70% -> NEUTRAL
    3. Mixed positive+negative words + "but" + POSITIVE
       sentiment + confidence < 70% -> NEUTRAL
    """
    text_lower = text.lower().strip()
    if not text_lower:
        return sentiment, confidence, False

    # Rule 1: Double negative correction
    # Applies to NEGATIVE sentiment OR low-confidence POSITIVE
    if sentiment in ("negative", "positive"):
        for pattern in _DOUBLE_NEG_RE:
            if pattern.search(text_lower):
                return "neutral", min(confidence, 65.0), True

    # Rule 2: Mixed "but" clause — NEGATIVE with low conf
    if (sentiment == "negative"
            and confidence < _BUT_CLAUSE_CONF_THRESHOLD):
        words = set(re.findall(r'\b\w+\b', text_lower))
        has_positive = bool(words & _POSITIVE_WORDS)
        has_but = bool(_BUT_WORDS.search(text_lower))
        if has_positive and has_but:
            return "neutral", min(confidence, 60.0), True

    # Rule 3: Mixed "but" clause — POSITIVE with low conf
    # (e.g., "Great food but slow service" -> positive 70.8%)
    if (sentiment == "positive"
            and confidence < _BUT_CLAUSE_CONF_THRESHOLD):
        words = set(re.findall(r'\b\w+\b', text_lower))
        has_positive = bool(words & _POSITIVE_WORDS)
        has_negative = bool(words & _NEGATIVE_WORDS)
        has_but = bool(_BUT_WORDS.search(text_lower))
        if has_positive and has_negative and has_but:
            return "neutral", min(confidence, 60.0), True

    return sentiment, confidence, False
