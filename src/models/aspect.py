"""Aspect-Based Sentiment Analysis — layered extraction + RoBERTa scoring.

Extraction layers (best-available):
  1. spaCy noun chunks  (if spacy + en_core_web_sm installed)
  2. TextBlob noun phrases  (if textblob installed)
  3. Built-in regex NP patterns + domain vocabulary  (always available)

Per-aspect sentiment is scored by the RoBERTa classifier.
"""

from __future__ import annotations

import re
import threading
from functools import lru_cache

import pandas as pd

# ── Domain-aspect seed vocabulary ────────────────────────────────────────────
# Common aspects across e-commerce, food, movie, and general product reviews.
# Used by the built-in fallback extractor.
_DOMAIN_ASPECTS = [
    # product quality
    "quality", "build quality", "material", "durability", "construction",
    "finish", "texture", "design", "appearance", "look", "weight",
    # delivery / shipping
    "delivery", "shipping", "packaging", "package", "box", "arrival",
    "tracking", "courier", "speed",
    # price / value
    "price", "value", "cost", "deal", "worth", "money", "budget",
    # performance
    "performance", "speed", "battery", "battery life", "power",
    "charging", "processor", "memory", "storage", "camera",
    "screen", "display", "resolution", "brightness", "color",
    # service / support
    "service", "support", "customer service", "customer support",
    "return", "refund", "seller", "response",
    # food
    "taste", "flavor", "aroma", "smell", "portion", "serving",
    "freshness", "texture", "spice", "sweetness", "temperature",
    "portion size", "restaurant", "staff",
    # movie / content
    "acting", "performance", "story", "plot", "direction", "script",
    "music", "soundtrack", "cinematography", "visuals", "effects",
    "characters", "ending",
    # generic positive/negative nouns
    "experience", "product", "item", "order", "purchase",
    "size", "fit", "color",
]

# Build a set for fast lookup
_ASPECT_SET = {a.lower() for a in _DOMAIN_ASPECTS}

# ── Stop-word filter ──────────────────────────────────────────────────────────
_STOP_WORDS = {
    "a", "an", "the", "this", "that", "these", "those",
    "i", "me", "my", "we", "our", "you", "your", "they", "their",
    "it", "its", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need",
    "just", "very", "really", "quite", "so", "too", "also",
    "and", "but", "or", "nor", "for", "yet", "so", "both",
    "in", "on", "at", "by", "with", "about", "from", "to", "of",
    "up", "out", "no", "not", "more", "most", "than", "then",
    "here", "there", "when", "where", "who", "which", "what",
    "all", "any", "each", "every", "some", "other", "only",
    "same", "such", "own", "few", "over", "after", "before",
    "again", "further", "once", "how",
}

_TRAILING_COPULAS = {"am", "are", "be", "been", "being", "is", "was", "were"}


# ── Singleton model loader ────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_spacy():
    """Load spaCy en_core_web_sm if available."""
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:
        return None


# ── Text helpers ─────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    t = re.sub(r"\s+", " ", text.strip().lower())
    tokens = t.split()
    while tokens and tokens[-1] in _TRAILING_COPULAS:
        tokens.pop()
    return " ".join(tokens)


def _is_valid(chunk: str) -> bool:
    tokens = [t for t in re.findall(r"[A-Za-z']+", chunk.lower()) if t]
    if not 1 <= len(tokens) <= 4:
        return False
    if all(t in _STOP_WORDS for t in tokens):
        return False
    return True


# ── Extraction layers ─────────────────────────────────────────────────────────

def _extract_spacy(text: str) -> list[str] | None:
    """Layer 1: spaCy noun chunks. Returns None if spaCy not available."""
    nlp = _load_spacy()
    if nlp is None:
        return None
    try:
        doc = nlp(text)
        return [chunk.text for chunk in doc.noun_chunks]
    except Exception:
        return None


def _extract_textblob(text: str) -> list[str] | None:
    """Layer 2: TextBlob noun phrases. Returns None if TextBlob not available."""
    try:
        from textblob import TextBlob
        return list(TextBlob(text).noun_phrases)
    except Exception:
        return None


def _extract_builtin(text: str) -> list[str]:
    """Layer 3: Regex NP patterns + domain vocabulary (always available).

    Strategy:
    a) Match domain-aspect phrases that appear verbatim in the text.
    b) Use regex to find Adj+Noun patterns (e.g. "fast delivery").
    c) Use regex to find simple Noun patterns (2+ chars, non-stopword).
    """
    text_lower = text.lower()
    found: list[str] = []
    seen: set[str] = set()

    # (a) domain vocabulary scan
    for aspect in _DOMAIN_ASPECTS:
        if aspect in text_lower and aspect not in seen:
            seen.add(aspect)
            found.append(aspect)

    # (b) Adj+Noun patterns: "adjective noun" bigrams
    # simple pattern: word word where first is an adjective-like word
    adj_noun_re = re.compile(
        r'\b([a-z]+(?:ful|less|ive|ous|al|ish|able|ible|ent|ant|ic|ary|ory|y))'
        r'\s+([a-z]{3,})\b'
    )
    for m in adj_noun_re.finditer(text_lower):
        adj, noun = m.group(1), m.group(2)
        bigram = f"{adj} {noun}"
        if (noun not in _STOP_WORDS and bigram not in seen
                and len(noun) > 2):
            seen.add(bigram)
            found.append(bigram)

    # (c) Key nouns from sentences — words adjacent to sentiment adjectives
    sentiment_adj = {
        "good", "great", "excellent", "amazing", "bad", "terrible", "awful",
        "poor", "horrible", "disappointing", "fast", "slow", "quick",
        "cheap", "expensive", "high", "low", "long", "short", "easy",
        "difficult", "hard", "smooth", "rough", "clear", "dark", "bright",
        "comfortable", "uncomfortable", "nice", "ugly", "beautiful",
        "broken", "perfect", "strong", "weak", "heavy", "light",
    }
    words = re.findall(r'\b[a-z]{3,}\b', text_lower)
    for i, word in enumerate(words):
        if word in sentiment_adj:
            # grab adjacent nouns (prev or next word)
            for j in (i - 1, i + 1):
                if 0 <= j < len(words):
                    candidate = words[j]
                    if (candidate not in _STOP_WORDS
                            and candidate not in sentiment_adj
                            and candidate not in seen
                            and len(candidate) > 2):
                        seen.add(candidate)
                        found.append(candidate)

    return found


def extract_aspects(text: str) -> list[str]:
    """Extract noun-chunk aspects using best available method."""
    text = str(text or "").strip()
    if not text:
        return []

    # Try each layer
    raw: list[str] | None = _extract_spacy(text)
    if raw is None:
        raw = _extract_textblob(text)
    if raw is None:
        raw = _extract_builtin(text)

    seen: set[str] = set()
    aspects: list[str] = []
    for chunk in raw:
        norm = _normalize(chunk)
        if not _is_valid(norm) or norm in seen:
            continue
        seen.add(norm)
        aspects.append(norm)

    return aspects


def _find_context_sentence(text: str, aspect: str) -> str:
    """Find the sentence most likely containing the aspect."""
    sentences = re.split(r'[.!?]+', text)
    for sent in sentences:
        if aspect.lower() in sent.lower():
            return sent.strip()
    return text


def analyze_aspects(text: str) -> list[dict]:
    """Extract aspects and run RoBERTa sentiment on each in context.

    Returns list of dicts: aspect, sentiment_label, polarity, subjectivity.
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
    seen_aspects: set[str] = set()
    for aspect in aspects:
        # De-duplicate and cap to 8 aspects for performance
        if aspect in seen_aspects or len(results) >= 8:
            break
        seen_aspects.add(aspect)

        context = _find_context_sentence(text, aspect)
        aspect_input = f"{aspect}: {context}"

        try:
            pred = sentiment_predict(aspect_input)
            scores = pred.get("scores", [0.0, 1.0, 0.0])  # [neg, neu, pos]
            polarity = scores[2] - scores[0]           # positive - negative
            results.append({
                "aspect": aspect,
                "sentiment_label": pred.get("label_name", "Neutral"),
                "polarity": round(polarity, 4),
                "subjectivity": round(1.0 - scores[1], 4),  # 1 - neutral
            })
        except Exception:
            continue

    # Sort by absolute polarity (most opinionated first)
    results.sort(key=lambda x: abs(x["polarity"]), reverse=True)
    return results


def get_aspect_dataframe(text: str) -> pd.DataFrame:
    """Analyze aspects and return as a formatted DataFrame."""
    rows = analyze_aspects(text)
    if not rows:
        return pd.DataFrame(
            columns=["Aspect", "Sentiment", "Polarity", "Subjectivity"]
        )

    df = pd.DataFrame(rows).rename(columns={
        "aspect": "Aspect",
        "sentiment_label": "Sentiment",
        "polarity": "Polarity",
        "subjectivity": "Subjectivity",
    })
    return df[["Aspect", "Sentiment", "Polarity", "Subjectivity"]]
