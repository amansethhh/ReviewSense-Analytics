"""Aspect-based sentiment analysis helpers for ReviewSense Analytics."""

from __future__ import annotations

import re
from functools import lru_cache

import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from textblob import TextBlob

STOP_WORDS = set(ENGLISH_STOP_WORDS)
TRAILING_COPULAS = {"am", "are", "be", "been", "being", "is", "was", "were"}


@lru_cache(maxsize=1)
def _load_spacy_model():
    try:
        import spacy
    except Exception:
        return None

    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        return None


def _normalize_aspect_text(aspect_text: str) -> str:
    normalized_text = re.sub(r"\s+", " ", aspect_text.strip().lower())
    tokens = normalized_text.split()

    while tokens and tokens[-1] in TRAILING_COPULAS:
        tokens.pop()

    return " ".join(tokens)


def _is_valid_chunk(chunk_text: str) -> bool:
    tokens = [token for token in re.findall(r"[A-Za-z']+", chunk_text.lower()) if token]
    if not 1 <= len(tokens) <= 3:
        return False
    if not tokens:
        return False
    if all(token in STOP_WORDS for token in tokens):
        return False
    return True


def _fallback_candidate_chunks(text: str) -> list[str]:
    fallback_chunks: list[str] = []

    try:
        noun_phrases = TextBlob(text).noun_phrases
        fallback_chunks.extend(noun_phrases)
    except Exception:
        pass

    if not fallback_chunks:
        determiner_pattern = re.compile(
            r"\b(?:the|a|an|this|that|these|those|my|your|our|their|its)\s+([a-zA-Z']+(?:\s+[a-zA-Z']+){0,1})",
            re.IGNORECASE,
        )
        fallback_chunks.extend(match.group(1) for match in determiner_pattern.finditer(text))

    if not fallback_chunks:
        tokens = [token for token in re.findall(r"[A-Za-z']+", text.lower()) if token not in STOP_WORDS]
        fallback_chunks.extend(tokens)

    return fallback_chunks


def _aspect_sentiment_label(polarity: float) -> str:
    if polarity > 0.1:
        return "Positive"
    if polarity < -0.1:
        return "Negative"
    return "Neutral"


def extract_aspects(text):
    """Use spaCy en_core_web_sm to extract noun chunks from text."""

    source_text = str(text or "").strip()
    if not source_text:
        return []

    nlp = _load_spacy_model()
    if nlp is not None:
        doc = nlp(source_text)
        raw_chunks = [chunk.text for chunk in doc.noun_chunks]
    else:
        raw_chunks = _fallback_candidate_chunks(source_text)

    aspects = []
    seen_aspects: set[str] = set()

    for chunk_text in raw_chunks:
        normalized_aspect = _normalize_aspect_text(chunk_text)
        if not _is_valid_chunk(normalized_aspect):
            continue
        if normalized_aspect in seen_aspects:
            continue

        sentiment = TextBlob(normalized_aspect).sentiment
        seen_aspects.add(normalized_aspect)
        aspects.append(
            {
                "aspect": normalized_aspect,
                "sentiment_label": _aspect_sentiment_label(sentiment.polarity),
                "polarity": float(sentiment.polarity),
                "subjectivity": float(sentiment.subjectivity),
            }
        )

    return aspects


def get_aspect_dataframe(text):
    """Call extract_aspects(), return a sorted pandas DataFrame."""

    aspect_rows = extract_aspects(text)
    if not aspect_rows:
        return pd.DataFrame(columns=["Aspect", "Sentiment", "Polarity", "Subjectivity"])

    aspect_df = pd.DataFrame(aspect_rows).rename(
        columns={
            "aspect": "Aspect",
            "sentiment_label": "Sentiment",
            "polarity": "Polarity",
            "subjectivity": "Subjectivity",
        }
    )
    aspect_df = aspect_df.sort_values(
        by="Polarity",
        key=lambda series: series.abs(),
        ascending=False,
    ).reset_index(drop=True)

    return aspect_df.loc[:, ["Aspect", "Sentiment", "Polarity", "Subjectivity"]]
