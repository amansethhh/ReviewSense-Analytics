"""Sarcasm detection — RoBERTa irony model + rule-based bulk detection.

Contains:
  1. detect_sarcasm()      — single prediction (RoBERTa model-based)
  2. detect_sarcasm_bulk() — bulk-safe version (rule-based, no star rating)
  3. Shared constants: SARCASM_PHRASES, NEGATIVE_LEXICON, HEDGE_PHRASES
  4. Exclusion guards to prevent false positives (ADD-ON 7)
"""

from __future__ import annotations

import re
import logging

logger = logging.getLogger("reviewsense")

# ═══════════════════════════════════════════════════════════════
# SHARED CONSTANTS
# ═══════════════════════════════════════════════════════════════

# Signal 1 — Ironic phrase markers (exact match, case-insensitive)
SARCASM_PHRASES = [
    "oh great", "just what i needed", "wow thanks", "what a surprise",
    "absolutely perfect", "couldn't be happier", "best ever", "so helpful",
    "totally worth it", "great job", "oh wonderful", "wow amazing",
    "what great quality", "works perfectly of course", "exactly as expected",
]

# Signal 2 — Strong negative lexicon for contradiction detection
NEGATIVE_LEXICON = {
    "terrible", "broken", "useless", "awful", "waste", "worst",
    "horrible", "dreadful", "disgusting", "pathetic", "garbage",
    "rubbish", "defective", "faulty", "fraud", "scam", "joke",
}

# ADD-ON 7 — Hedge phrases for false positive exclusion
# Defined ONCE here and imported by other modules if needed
HEDGE_PHRASES = [
    "okay", "ok", "alright", "fine", "decent", "average", "acceptable",
    "reasonable", "adequate", "sufficient", "not bad", "not great",
    "not amazing", "nothing special", "nothing impressive", "gets the job done",
    "does what it says", "does the job", "works fine", "serves its purpose",
    "could be better", "not the best", "not the worst", "functional",
    "passable", "tolerable", "mediocre", "fair enough", "so-so",
    "nothing memorable", "just average", "works most of the time",
    "nothing to complain about", "nothing to rave about", "basic",
    "does what it claims", "standard quality", "standard product",
]


# ═══════════════════════════════════════════════════════════════
# EXCLUSION GUARDS (ADD-ON 7)
# ═══════════════════════════════════════════════════════════════

def _contains_hedge(text: str) -> bool:
    """Reusable hedge phrase detector."""
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in HEDGE_PHRASES)


def _sarcasm_exclusion_check(text: str, confidence: float) -> dict | None:
    """Returns early-exit dict if text should NOT be evaluated for sarcasm.

    Returns None to proceed with full sarcasm detection.
    Guards against:
      - Very short texts (< 5 words)
      - Low confidence predictions (< 0.55)
      - Genuine hedge/neutral phrases
    """
    if len(text.split()) < 5:
        return {"is_sarcastic": False, "confidence": 0.0,
                "reason": "too_short", "severity": "none"}
    if confidence < 0.55:
        return {"is_sarcastic": False, "confidence": 0.0,
                "reason": "low_confidence_excluded", "severity": "none"}
    if _contains_hedge(text):
        return {"is_sarcastic": False, "confidence": 0.0,
                "reason": "hedge_phrase_excluded", "severity": "none"}
    return None  # proceed with full detection


# ═══════════════════════════════════════════════════════════════
# SINGLE PREDICTION — detect_sarcasm()
# ═══════════════════════════════════════════════════════════════

def detect_sarcasm(text, predicted_label=None, star_rating=None):
    """Detect sarcasm using RoBERTa irony classifier.

    predicted_label and star_rating are kept for backward compatibility.
    Falls back to rules-based if transformer model is unavailable.

    Modified threshold: contradiction detection fires at 0.82 (was 0.90).
    """
    text = str(text or "").strip()
    if not text:
        return {
            "is_sarcastic": False,
            "confidence": 0.0,
            "reason": "No text provided.",
            "severity": "low",
        }

    # ADD-ON 7 — Exclusion guard (fires first)
    # Use a default confidence of 0.80 for single prediction exclusion check
    early = _sarcasm_exclusion_check(text, 0.80)
    if early is not None:
        return early

    try:
        from src.models.sarcasm_model import predict as irony_predict
        result = irony_predict(text)
        if result.get("is_sarcastic", False):
            return result
    except Exception as e:
        logger.warning("Sarcasm model fallback to rules: %s", e)

    # R4: Regex-based contradiction patterns (always checked)
    return _rules_with_regex_fallback(text, predicted_label, star_rating)


def _rules_fallback(text, predicted_label, star_rating):
    """Simple rules-based fallback if transformer is unavailable."""
    try:
        from textblob import TextBlob
        polarity = TextBlob(text).sentiment.polarity
    except Exception:
        polarity = 0.0

    label = int(predicted_label or 1)
    star = float(star_rating) if star_rating is not None else None

    # Contradiction: positive wording + negative prediction
    if polarity > 0.35 and label == 0:
        return {"is_sarcastic": True, "confidence": 0.7,
                "reason": "Positive wording with negative prediction.",
                "severity": "medium"}

    # Star-sentiment contradiction
    if star is not None and star <= 2 and polarity > 0.5:
        return {"is_sarcastic": True, "confidence": 0.75,
                "reason": "Low stars with positive wording.",
                "severity": "high"}

    return {"is_sarcastic": False, "confidence": 0.05,
            "reason": "No sarcasm indicators detected.",
            "severity": "low"}


# R4: Regex-based sarcasm patterns for obvious contradictions
_SARCASM_REGEX_PATTERNS = [
    re.compile(
        r'\boh\s+(great|wonderful|fantastic|perfect|brilliant|amazing)\b',
        re.IGNORECASE,
    ),
    re.compile(
        r'\b(amazing|excellent|superb|wonderful|perfect)\b.*\b(worst|terrible|awful|broke|failed|useless|waste)\b',
        re.IGNORECASE,
    ),
    re.compile(
        r'\bwhat\s+a\s+(great|wonderful|perfect|fantastic)\s+(product|item|purchase)\b',
        re.IGNORECASE,
    ),
    re.compile(
        r'\b(great|wonderful|fantastic)\b.*\b(stopped working|broke|broken|died|dead)\b',
        re.IGNORECASE,
    ),
]


def _rules_with_regex_fallback(text, predicted_label, star_rating):
    """R4: Combined regex pattern + rules-based sarcasm detection."""
    text_lower = text.lower()

    # Check regex patterns first
    for pattern in _SARCASM_REGEX_PATTERNS:
        if pattern.search(text_lower):
            logger.warning("Sarcasm detected (regex): '%s'", text[:80])
            return {
                "is_sarcastic": True,
                "confidence": 0.80,
                "reason": "Contradictory language pattern detected.",
                "severity": "medium",
            }

    # Fall through to traditional rules
    return _rules_fallback(text, predicted_label, star_rating)


# ═══════════════════════════════════════════════════════════════
# BULK DETECTION — detect_sarcasm_bulk()
# ═══════════════════════════════════════════════════════════════

def detect_sarcasm_bulk(text: str, pred_class: int, confidence: float) -> dict:
    """Bulk-safe sarcasm detection without star rating.

    Uses three linguistic signals:
      Signal 1: Ironic phrase markers
      Signal 2: High-confidence Positive + strong negative lexicon
      Signal 3: Overstatement with negative content (3+ exclamation marks)

    Args:
        text: Review text to analyze.
        pred_class: Predicted sentiment class (0/1/2).
        confidence: Model confidence score.

    Returns dict with: is_sarcastic, confidence, reason, severity.
    """
    text = str(text or "").strip()
    if not text:
        return {"is_sarcastic": False, "confidence": 0.0,
                "reason": "None", "severity": "none"}

    # ADD-ON 7 — Exclusion guard (fires first)
    early = _sarcasm_exclusion_check(text, confidence)
    if early is not None:
        return early

    text_lower = text.lower()
    text_tokens = set(text_lower.split())

    # Signal 1 — Ironic phrase markers (exact match, case-insensitive)
    signal_1 = any(phrase in text_lower for phrase in SARCASM_PHRASES)

    # Signal 2 — High-confidence Positive + strong negative lexicon
    signal_2 = (
        pred_class == 2
        and confidence > 0.82
        and bool(text_tokens & NEGATIVE_LEXICON)
    )

    # Signal 3 — Overstatement with negative content (3+ exclamation marks)
    signal_3 = (
        text.count("!") >= 3
        and bool(text_tokens & NEGATIVE_LEXICON)
    )

    # Combined decision
    is_sarcastic = signal_1 or signal_2 or signal_3

    if not is_sarcastic:
        return {"is_sarcastic": False, "confidence": 0.0,
                "reason": "None", "severity": "none"}

    # Determine primary reason
    if signal_1:
        reason = "Ironic phrase detected"
    elif signal_2:
        reason = "Sentiment contradiction"
    else:
        reason = "Overstatement with negative content"

    logger.warning("Sarcasm detected (bulk): %s — '%s'", reason, text[:80])

    return {
        "is_sarcastic": True,
        "confidence": 0.75,
        "reason": reason,
        "severity": "medium",
    }
