"""
Tests for apply_sentiment_corrections() shared utility.
Covers double negatives, but-clauses, and edge cases.
"""
import pytest
from backend.app.sentiment_corrections import (
    apply_sentiment_corrections,
)


@pytest.mark.parametrize("text,input_sent,input_conf,expected", [
    # Double negatives — must correct to neutral
    ("not bad",                     "negative", 73.8, "neutral"),
    ("not terrible at all",         "negative", 80.0, "neutral"),
    ("not awful",                   "negative", 65.0, "neutral"),
    ("not terrible at all",         "positive", 37.7, "neutral"),
    # But-clause mixed — negative with low conf
    ("Good product but overpriced", "negative", 59.2, "neutral"),
    ("Great food but slow service", "negative", 62.0, "neutral"),
    # But-clause mixed — positive with low conf
    ("Great food but slow service",    "positive", 55.0, "neutral"),
    ("Amazing quality but expensive",  "positive", 51.9, "neutral"),
    # Should NOT be corrected
    ("absolutely terrible",         "negative", 95.0, "negative"),
    ("loved every moment",          "positive", 97.0, "positive"),
    # High conf but-clause — no correction
    ("Good product but overpriced", "negative", 85.0, "negative"),
])
def test_corrections(text, input_sent, input_conf, expected):
    result_sent, _, _ = apply_sentiment_corrections(
        text, input_sent, input_conf)
    assert result_sent == expected, (
        f"'{text}': expected {expected}, got {result_sent}"
    )


def test_positive_never_corrected_when_high_conf():
    sent, conf, was_corrected = apply_sentiment_corrections(
        "amazing product", "positive", 98.0
    )
    assert sent == "positive"
    assert not was_corrected


def test_high_confidence_but_clause_not_corrected():
    sent, _, was_corrected = apply_sentiment_corrections(
        "great product but expensive", "negative", 80.0
    )
    assert sent == "negative"
    assert not was_corrected


def test_empty_text_returns_unchanged():
    sent, conf, was_corrected = apply_sentiment_corrections(
        "", "positive", 50.0
    )
    assert sent == "positive"
    assert not was_corrected


def test_correction_caps_confidence():
    """When corrected, confidence should be capped."""
    sent, conf, was_corrected = apply_sentiment_corrections(
        "not bad", "negative", 73.8
    )
    assert sent == "neutral"
    assert conf <= 65.0
    assert was_corrected
