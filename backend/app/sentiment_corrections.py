"""
Shared sentiment correction utilities.
Applied post-prediction in both /predict and /language routes.
Corrects known model weaknesses:
  - Double negatives: "not bad" -> NEUTRAL when model says NEGATIVE
  - Mixed "but" clauses: "good but expensive" -> NEUTRAL
  - S2: Neutral zone — confidence-gated + keyword override
  - S3: Strong negative keyword override
  - A1: ABSA reconciler
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

# S2: Neutral signal phrases (whole-word match)
NEUTRAL_SIGNALS = [
    "okay", "ok", "alright", "fine", "decent", "average", "adequate",
    "acceptable", "reasonable", "standard", "mediocre", "nothing special",
    "nothing impressive", "nothing exceptional", "does the job",
    "gets the job done", "not bad", "not great", "nothing memorable",
    "basic", "functional", "does what it says",
]

# S3: Strong negative signal phrases (whole-word match)
STRONG_NEGATIVE_SIGNALS = [
    "complete failure", "did not work", "awful", "useless",
    "complete waste", "worst", "terrible", "dreadful", "broke",
    "defective", "broken", "horrible", "appalling", "not impressed",
    "far below", "not worth", "avoid",
]


def _match_signal(text_lower: str, signals: list[str]) -> bool:
    """Check if any signal phrase appears as a whole-word match."""
    for signal in signals:
        pattern = r'\b' + re.escape(signal) + r'\b'
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


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
    4. S2: Neutral zone — keyword + confidence gate
    5. S3: Strong negative keyword override
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

    # S3: Strong negative override — catches clear negatives
    # mislabelled as NEUTRAL or POSITIVE at moderate confidence
    if sentiment != "negative" and confidence < 85.0:
        if _match_signal(text_lower, STRONG_NEGATIVE_SIGNALS):
            logger.info(
                "[OVERRIDE] Strong negative keyword rule applied: "
                "'%s' -> NEGATIVE", text[:60]
            )
            return "negative", max(confidence, 70.0), True

    # S2: Neutral zone — confidence-gated + keyword override
    # Only applies to borderline POSITIVE predictions
    if sentiment == "positive" and confidence < 55.0:
        # Low-confidence positive in neutral polarity zone
        logger.info(
            "[OVERRIDE] Neutral zone (low confidence): "
            "'%s' -> NEUTRAL", text[:60]
        )
        return "neutral", max(confidence, 40.0), True

    if sentiment == "positive" and confidence < 70.0:
        if _match_signal(text_lower, NEUTRAL_SIGNALS):
            logger.info(
                "[OVERRIDE] Neutral keyword rule applied: "
                "'%s' -> NEUTRAL", text[:60]
            )
            return "neutral", max(confidence, 45.0), True

    return sentiment, confidence, False


def reconcile_absa_with_headline(
    headline_sentiment: str,
    headline_confidence: float,
    absa_aspects: list[dict] | None,
) -> Tuple[str, bool]:
    """
    A1: ABSA reconciler — overrides headline sentiment when
    ALL ABSA aspects unanimously disagree.

    Never overrides high-confidence (>=90%) predictions.

    Returns:
        (reconciled_sentiment, was_reconciled)
    """
    if not absa_aspects or headline_confidence >= 90.0:
        return headline_sentiment, False

    polarities = [a.get("polarity", 0.0) for a in absa_aspects]
    if not polarities:
        return headline_sentiment, False

    neg_count = sum(1 for p in polarities if p < -0.1)
    pos_count = sum(1 for p in polarities if p > 0.1)
    avg_pol = sum(polarities) / len(polarities)

    # All aspects negative but headline says POSITIVE/NEUTRAL
    if (neg_count == len(polarities)
            and headline_sentiment in ("positive", "neutral")
            and avg_pol < -0.3):
        logger.info(
            "[ABSA-RECONCILE] Headline overridden: %s -> NEGATIVE "
            "(avg_polarity=%.3f, %d aspects)",
            headline_sentiment.upper(), avg_pol, len(polarities),
        )
        return "negative", True

    # All aspects positive but headline says NEGATIVE/NEUTRAL
    if (pos_count == len(polarities)
            and headline_sentiment in ("negative", "neutral")
            and avg_pol > 0.3):
        logger.info(
            "[ABSA-RECONCILE] Headline overridden: %s -> POSITIVE "
            "(avg_polarity=%.3f, %d aspects)",
            headline_sentiment.upper(), avg_pol, len(polarities),
        )
        return "positive", True

    return headline_sentiment, False
