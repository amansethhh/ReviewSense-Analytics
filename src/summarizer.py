"""Summarization utilities for ReviewSense Analytics."""

from __future__ import annotations

import re
from typing import Iterable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from textblob import TextBlob
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer


def _normalize_reviews(reviews_list: Iterable[str]) -> list[str]:
    return [str(review).strip() for review in reviews_list if str(review).strip()]


def _filter_by_aspect(reviews_list: list[str], aspect: str | None) -> list[str]:
    if not aspect:
        return reviews_list

    aspect_pattern = re.compile(re.escape(str(aspect).strip().lower()))
    return [review for review in reviews_list if aspect_pattern.search(review.lower())]


def _ensure_sumy_tokenizer() -> None:
    try:
        import nltk
    except Exception:
        return

    for resource in ("punkt", "punkt_tab"):
        try:
            nltk.data.find(f"tokenizers/{resource}")
        except LookupError:
            try:
                nltk.download(resource, quiet=True)
            except Exception:
                pass


def summarize_reviews(reviews_list, num_sentences=3, aspect=None) -> str:
    """Combine reviews_list into one document and summarize it."""

    normalized_reviews = _normalize_reviews(reviews_list)
    filtered_reviews = _filter_by_aspect(normalized_reviews, aspect)

    if not filtered_reviews:
        return "No reviews to summarize."

    if len(filtered_reviews) < 3:
        return " ".join(filtered_reviews)

    combined_document = " ".join(filtered_reviews)
    _ensure_sumy_tokenizer()

    parser = PlaintextParser.from_string(combined_document, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary_sentences = summarizer(parser.document, sentences_count=max(1, int(num_sentences)))
    summary_text = " ".join(str(sentence) for sentence in summary_sentences).strip()

    return summary_text or " ".join(filtered_reviews[:num_sentences])


def _top_phrases_for_subset(texts: list[str], n: int) -> list[str]:
    if not texts:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=1000,
    )
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return []

    feature_names = np.asarray(vectorizer.get_feature_names_out())
    scores = np.asarray(tfidf_matrix.mean(axis=0)).ravel()

    top_indices = scores.argsort()[::-1]
    top_phrases: list[str] = []
    for index in top_indices:
        phrase = feature_names[index].strip()
        if not phrase or phrase in top_phrases:
            continue
        top_phrases.append(phrase)
        if len(top_phrases) == n:
            break

    return top_phrases


def get_top_phrases(reviews_list, n=5) -> tuple:
    """Extract top n positive phrases and top n negative phrases."""

    normalized_reviews = _normalize_reviews(reviews_list)
    if not normalized_reviews:
        return ([], [])

    positive_reviews = [
        review
        for review in normalized_reviews
        if TextBlob(review).sentiment.polarity > 0.1
    ]
    negative_reviews = [
        review
        for review in normalized_reviews
        if TextBlob(review).sentiment.polarity < -0.1
    ]

    positive_phrases = _top_phrases_for_subset(positive_reviews, n)
    negative_phrases = _top_phrases_for_subset(negative_reviews, n)

    return positive_phrases, negative_phrases
