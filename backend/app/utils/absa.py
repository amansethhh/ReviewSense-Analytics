"""
Enhanced ABSA (Aspect-Based Sentiment Analysis) module.

BUG-4 FIX: Resolves broken aspect extraction by using:
1. spaCy noun chunk extraction (not just keyword matching)
2. Keyword-based aspect categorization
3. Polarity-based sentiment aggregation (not dominant label mode)
4. Per-aspect sentence-level sentiment via TextBlob

All routes import from here — single source of truth for ABSA.
"""

from __future__ import annotations

import re
import logging
from typing import Optional

logger = logging.getLogger("reviewsense.absa_enhanced")


# ═══════════════════════════════════════════════════════════════
# Aspect keyword taxonomy
# ═══════════════════════════════════════════════════════════════

ASPECT_KEYWORDS = {
    "product": [
        "product", "item", "thing", "purchase", "buy", "order",
        "unit", "piece", "goods",
    ],
    "quality": [
        "quality", "build", "material", "durability", "construction",
        "craftsmanship", "finish", "sturdy", "flimsy", "solid",
        "durable", "fragile",
    ],
    "price": [
        "price", "cost", "value", "expensive", "cheap", "worth",
        "money", "affordable", "overpriced", "budget", "pricey",
        "bargain",
    ],
    "service": [
        "service", "support", "customer", "help", "response",
        "delivery", "shipping", "return", "refund", "warranty",
        "staff", "representative",
    ],
    "design": [
        "design", "look", "appearance", "style", "aesthetic",
        "color", "colour", "size", "shape", "form", "sleek",
        "elegant", "ugly",
    ],
    "performance": [
        "performance", "speed", "fast", "slow", "efficiency",
        "works", "function", "functionality", "reliable",
        "battery", "power",
    ],
    "packaging": [
        "packaging", "box", "wrapped", "arrived", "condition",
        "package", "unboxing",
    ],
    "usability": [
        "easy", "simple", "intuitive", "complicated", "confusing",
        "user-friendly", "convenient", "difficult", "setup",
        "interface", "instructions",
    ],
}


def _load_spacy():
    """Load spaCy model with fallback download."""
    try:
        import spacy
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            logger.warning(
                "spaCy en_core_web_sm not found, downloading...")
            import subprocess
            subprocess.check_call([
                "python", "-m", "spacy", "download", "en_core_web_sm"
            ])
            return spacy.load("en_core_web_sm")
    except (ImportError, Exception) as e:
        logger.error("spaCy not installed or failed to initialize: %s", e)
        return None


# Lazy-loaded spaCy model
_NLP_CACHE = {}


def _get_nlp():
    if "nlp" not in _NLP_CACHE:
        _NLP_CACHE["nlp"] = _load_spacy()
    return _NLP_CACHE["nlp"]


# ═══════════════════════════════════════════════════════════════
# Aspect extraction
# ═══════════════════════════════════════════════════════════════

def extract_aspects_enhanced(text: str) -> list[str]:
    """Enhanced aspect extraction using spaCy noun chunks + keyword matching.

    Returns list of unique aspect category names (e.g., "quality", "price").
    """
    text_lower = text.lower()
    extracted = []

    # Method 1: Keyword matching
    for aspect, keywords in ASPECT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                if aspect not in extracted:
                    extracted.append(aspect)
                break  # one match per aspect is enough

    # Method 2: spaCy noun chunk extraction (additional aspects)
    nlp = _get_nlp()
    if nlp:
        try:
            doc = nlp(text_lower)
            noun_phrases = [chunk.text.strip() for chunk in doc.noun_chunks]

            for phrase in noun_phrases:
                for aspect, keywords in ASPECT_KEYWORDS.items():
                    if aspect not in extracted:
                        if any(kw in phrase for kw in keywords):
                            extracted.append(aspect)
        except Exception as e:
            logger.warning("spaCy noun chunk extraction failed: %s", e)

    # Default: at least "product" if nothing found
    if not extracted:
        extracted = ["product"]

    return extracted


# ═══════════════════════════════════════════════════════════════
# Per-aspect sentiment analysis
# ═══════════════════════════════════════════════════════════════

def analyze_aspect_sentiment(
    text: str,
    aspect: str,
) -> dict:
    """Analyze sentiment for a specific aspect using TextBlob polarity.

    BUG-4 FIX: Uses polarity score, not just pos/neg/neutral labels.
    Extracts sentences mentioning the aspect for focused analysis.
    """
    from textblob import TextBlob

    text_lower = text.lower()
    aspect_keywords = ASPECT_KEYWORDS.get(aspect, [aspect])

    # Find sentences mentioning this aspect
    nlp = _get_nlp()
    aspect_sentences = []

    if nlp:
        try:
            doc = nlp(text)
            for sent in doc.sents:
                sent_lower = sent.text.lower()
                if any(kw in sent_lower for kw in aspect_keywords):
                    aspect_sentences.append(sent.text)
        except Exception:
            pass

    # Fallback: use whole text if no specific sentences found
    if not aspect_sentences:
        aspect_sentences = [text]

    # Calculate average polarity across aspect sentences
    polarities = []
    subjectivities = []
    for sentence in aspect_sentences:
        blob = TextBlob(sentence)
        polarities.append(blob.sentiment.polarity)
        subjectivities.append(blob.sentiment.subjectivity)

    avg_polarity = (
        sum(polarities) / len(polarities) if polarities else 0.0
    )
    avg_subjectivity = (
        sum(subjectivities) / len(subjectivities)
        if subjectivities else 0.5
    )

    # Map polarity to sentiment with proper thresholds
    if avg_polarity > 0.1:
        sentiment = "POSITIVE"
        confidence = min(95.0, 50 + abs(avg_polarity) * 45)
    elif avg_polarity < -0.1:
        sentiment = "NEGATIVE"
        confidence = min(95.0, 50 + abs(avg_polarity) * 45)
    else:
        sentiment = "NEUTRAL"
        confidence = 40 + (1 - abs(avg_polarity)) * 20

    return {
        "aspect": aspect,
        "sentiment": sentiment.lower(),
        "sentiment_label": sentiment,
        "confidence": round(confidence, 1),
        "polarity": round(avg_polarity, 3),
        "subjectivity": round(avg_subjectivity, 3),
        "mentions": len(aspect_sentences),
    }


# ═══════════════════════════════════════════════════════════════
# Complete ABSA pipeline
# ═══════════════════════════════════════════════════════════════

def perform_absa(text: str) -> dict:
    """Complete ABSA pipeline with polarity-based aggregation.

    BUG-4 FIX: Uses polarity sum for overall sentiment,
    NOT mode of aspect labels (which collapsed to neutral).

    Returns dict with:
      aspects: list of per-aspect results
      overall_sentiment: aggregated from polarity sum
      overall_confidence: average of aspect confidences
      total_polarity: sum of aspect polarities
      aspect_count: number of aspects found
    """
    # Extract aspects
    aspects = extract_aspects_enhanced(text)

    # Analyze sentiment for each aspect
    aspect_results = []
    polarities = []

    for aspect in aspects:
        result = analyze_aspect_sentiment(text, aspect)
        aspect_results.append(result)
        polarities.append(result["polarity"])

    # Aggregate using POLARITY SUM, not dominant label
    total_polarity = sum(polarities)

    if total_polarity > 0.1:
        overall = "positive"
    elif total_polarity < -0.1:
        overall = "negative"
    else:
        overall = "neutral"

    avg_confidence = (
        sum(a["confidence"] for a in aspect_results)
        / len(aspect_results)
        if aspect_results else 50.0
    )

    return {
        "aspects": aspect_results,
        "overall_sentiment": overall,
        "overall_confidence": round(avg_confidence, 1),
        "total_polarity": round(total_polarity, 3),
        "aspect_count": len(aspects),
    }
