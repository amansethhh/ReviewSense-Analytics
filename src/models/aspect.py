"""Aspect-Based Sentiment Analysis — spaCy extraction + RoBERTa scoring.

Extracts noun-chunk aspects via spaCy, then runs the RoBERTa sentiment
model on each "aspect: context sentence" to get real polarity scores.
"""

from __future__ import annotations

import re
from functools import lru_cache

import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

STOP_WORDS = set(ENGLISH_STOP_WORDS)
TRAILING_COPULAS = {"am", "are", "be", "been", "being", "is", "was", "were"}


@lru_cache(maxsize=1)
def _load_spacy():
    """Load spaCy en_core_web_sm."""
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:
        return None


def _normalize(text: str) -> str:
    t = re.sub(r"\s+", " ", text.strip().lower())
    tokens = t.split()
    while tokens and tokens[-1] in TRAILING_COPULAS:
        tokens.pop()
    return " ".join(tokens)


def _is_valid(chunk: str) -> bool:
    tokens = [t for t in re.findall(r"[A-Za-z']+", chunk.lower()) if t]
    if not 1 <= len(tokens) <= 4:
        return False
    if all(t in STOP_WORDS for t in tokens):
        return False
    return True


def _find_context_sentence(text: str, aspect: str) -> str:
    """Find the sentence containing the aspect."""
    sentences = re.split(r'[.!?]+', text)
    for sent in sentences:
        if aspect.lower() in sent.lower():
            return sent.strip()
    return text


def extract_aspects(text: str) -> list[str]:
    """Extract noun-chunk aspects from text using spaCy."""
    text = str(text or "").strip()
    if not text:
        return []

    nlp = _load_spacy()
    if nlp is not None:
        doc = nlp(text)
        raw = [chunk.text for chunk in doc.noun_chunks]
    else:
        # Fallback: simple noun phrase extraction
        try:
            from textblob import TextBlob
            raw = list(TextBlob(text).noun_phrases)
        except Exception:
            raw = []

    seen = set()
    aspects = []
    for chunk in raw:
        norm = _normalize(chunk)
        if not _is_valid(norm) or norm in seen:
            continue
        seen.add(norm)
        aspects.append(norm)

    return aspects


def analyze_aspects(text: str) -> list[dict]:
    """Extract aspects and run RoBERTa sentiment on each in context.

    Returns list of dicts with: aspect, sentiment, polarity, subjectivity.
    """
    text = str(text or "").strip()
    if not text:
        return []

    aspects = extract_aspects(text)
    if not aspects:
        return []

    # Import sentiment model for per-aspect scoring
    from src.models.sentiment import predict as sentiment_predict

    results = []
    for aspect in aspects:
        context = _find_context_sentence(text, aspect)
        # Run sentiment on "aspect: context" for focused scoring
        aspect_input = f"{aspect}: {context}"
        pred = sentiment_predict(aspect_input)

        # Map scores to polarity: positive_score - negative_score
        scores = pred["scores"]  # [neg, neu, pos]
        polarity = scores[2] - scores[0]  # positive - negative

        results.append({
            "aspect": aspect,
            "sentiment_label": pred["label_name"],
            "polarity": round(polarity, 4),
            "subjectivity": round(1.0 - scores[1], 4),  # 1 - neutral = subjectivity
        })

    # Sort by absolute polarity (most opinionated first)
    results.sort(key=lambda x: abs(x["polarity"]), reverse=True)
    return results


def get_aspect_dataframe(text: str) -> pd.DataFrame:
    """Analyze aspects and return as a formatted DataFrame."""
    rows = analyze_aspects(text)
    if not rows:
        return pd.DataFrame(columns=["Aspect", "Sentiment", "Polarity", "Subjectivity"])

    df = pd.DataFrame(rows).rename(columns={
        "aspect": "Aspect",
        "sentiment_label": "Sentiment",
        "polarity": "Polarity",
        "subjectivity": "Subjectivity",
    })
    return df[["Aspect", "Sentiment", "Polarity", "Subjectivity"]]
