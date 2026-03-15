"""Rules-based sarcasm detection for ReviewSense Analytics."""

from __future__ import annotations

from textblob import TextBlob


def detect_sarcasm(text, predicted_label, star_rating=None):
    """Detect sarcasm from sentiment mismatches and emphasis rules."""

    source_text = str(text or "").strip()
    if not source_text:
        return {
            "is_sarcastic": False,
            "confidence": 0.0,
            "reason": "No text provided.",
            "severity": "low",
        }

    label_value = int(predicted_label)
    star_value = float(star_rating) if star_rating is not None else None
    sentiment = TextBlob(source_text).sentiment
    polarity = float(sentiment.polarity)
    exclamation_count = source_text.count("!")

    triggered_rules = []

    if polarity > 0.35 and label_value == 0:
        triggered_rules.append(
            {
                "confidence": 0.9,
                "reason": "Positive wording conflicts with a negative model prediction.",
                "severity": "high",
            }
        )

    if polarity < -0.35 and label_value == 2:
        triggered_rules.append(
            {
                "confidence": 0.9,
                "reason": "Negative wording conflicts with a positive model prediction.",
                "severity": "high",
            }
        )

    if star_value is not None and star_value <= 2 and polarity > 0.5:
        triggered_rules.append(
            {
                "confidence": 0.95,
                "reason": "Low star rating paired with strongly positive wording suggests sarcasm.",
                "severity": "high",
            }
        )

    if exclamation_count > 2 and label_value == 0:
        triggered_rules.append(
            {
                "confidence": 0.65,
                "reason": "Heavy exclamation emphasis with a negative prediction suggests possible sarcasm.",
                "severity": "medium",
            }
        )

    if not triggered_rules:
        return {
            "is_sarcastic": False,
            "confidence": 0.05,
            "reason": "No sarcasm indicators detected.",
            "severity": "low",
        }

    strongest_rule = max(triggered_rules, key=lambda item: item["confidence"])
    combined_confidence = min(1.0, strongest_rule["confidence"] + 0.05 * (len(triggered_rules) - 1))

    return {
        "is_sarcastic": True,
        "confidence": float(combined_confidence),
        "reason": strongest_rule["reason"],
        "severity": strongest_rule["severity"],
    }
