"""Centralized analytics module for ReviewSense Analytics.

Single source of truth for metrics, summaries, keywords, and charts.
All pages import from here — NO duplicated logic.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

import pandas as pd
import plotly.graph_objects as go


# ━━━ CONSTANTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STOP_WORDS = {
    "the", "a", "an", "is", "was", "and", "to", "of", "in", "it",
    "for", "on", "this", "that", "with", "i", "my", "me", "but",
    "are", "at", "be", "have", "has", "had", "not", "or", "so",
    "if", "its", "do", "no", "just", "very", "all", "can", "will",
    "from", "they", "we", "you", "your", "he", "she", "as", "by",
}


# ━━━ METRICS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def compute_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """Compute sentiment metrics from a results DataFrame.

    Expects columns: Sentiment, Confidence, Polarity.
    Returns dict with total, pos, neg, neu, sarc_count, avg_conf, avg_pol.
    """
    total = len(df)
    pos = int((df["Sentiment"] == "Positive").sum()) if "Sentiment" in df.columns else 0
    neg = int((df["Sentiment"] == "Negative").sum()) if "Sentiment" in df.columns else 0
    neu = int((df["Sentiment"] == "Neutral").sum()) if "Sentiment" in df.columns else 0
    sarc_count = int((df["Sarcasm"] == "Yes").sum()) if "Sarcasm" in df.columns else 0
    avg_conf = float(df["Confidence"].mean()) if "Confidence" in df.columns else 0.0
    avg_pol = float(df["Polarity"].mean()) if "Polarity" in df.columns else 0.0

    return {
        "total": total,
        "pos": pos,
        "neg": neg,
        "neu": neu,
        "sarc_count": sarc_count,
        "avg_conf": avg_conf,
        "avg_pol": avg_pol,
    }


# ━━━ KEYWORDS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_keywords(
    texts: pd.Series,
    n: int = 12,
) -> list[tuple[str, int]]:
    """Extract top-n keywords from a Series of text, excluding stop words.

    Returns list of (word, count) tuples sorted by frequency.
    """
    words = re.findall(r'\b[a-z]{3,}\b', " ".join(texts.fillna("")).lower())
    return Counter(
        w for w in words if w not in STOP_WORDS
    ).most_common(n)


def extract_keywords_single(text: str, n: int = 10) -> list[tuple[str, int]]:
    """Extract keywords from a single text string."""
    words = re.findall(r'\b[a-z]{3,}\b', str(text).lower())
    return Counter(
        w for w in words if w not in STOP_WORDS
    ).most_common(n)


# ━━━ AI SUMMARY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_summary(df: pd.DataFrame, sarcasm_on: bool = False) -> str:
    """Generate structured AI summary from results DataFrame.

    Returns clean HTML string — no markdown symbols, no raw reviews.
    """
    m = compute_metrics(df)
    total, pos, neg, neu = m["total"], m["pos"], m["neg"], m["neu"]
    if total == 0:
        return "No data to summarize."

    pos_pct = pos / total * 100
    neg_pct = neg / total * 100
    neu_pct = neu / total * 100
    avg_conf = m["avg_conf"]
    avg_pol = m["avg_pol"]

    # Determine trend
    if pos_pct > 60:
        trend = "overwhelmingly positive"
    elif pos_pct > 45:
        trend = "generally positive"
    elif neg_pct > 45:
        trend = "predominantly negative"
    elif neu_pct > 50:
        trend = "largely neutral"
    else:
        trend = "mixed"

    conf_label = "high" if avg_conf > 75 else "moderate" if avg_conf > 55 else "low"
    pol_label = "positive leaning" if avg_pol > 0.1 else "negative leaning" if avg_pol < -0.1 else "balanced"

    H = '<span style="color:#00e5cc;font-weight:600;">'
    E = '</span>'
    lines = []
    lines.append(f'📈 {H}Overall Sentiment:{E} The dataset of {total:,} reviews shows a {trend} sentiment pattern.')
    lines.append(f'📊 {H}Distribution:{E} {pos_pct:.1f}% positive, {neg_pct:.1f}% negative, {neu_pct:.1f}% neutral.')
    lines.append(f'🎯 {H}Model Confidence:{E} Average confidence score is {avg_conf:.1f}%, indicating {conf_label} prediction reliability.')
    lines.append(f'📐 {H}Polarity Score:{E} Mean polarity is {avg_pol:.3f} ({pol_label}).')

    # Language diversity
    if "Language" in df.columns:
        unique_langs = df["Language"].nunique()
        if unique_langs > 1:
            top_lang = df["Language"].mode().iloc[0] if not df["Language"].mode().empty else "English"
            lines.append(f'🌐 {H}Language Diversity:{E} {unique_langs} languages detected. Primary language: {top_lang}.')

    # Sarcasm
    sarc_count = m["sarc_count"]
    if sarcasm_on and sarc_count > 0:
        sarc_pct = sarc_count / total * 100
        lines.append(f'🎭 {H}Sarcasm:{E} {sarc_count:,} reviews ({sarc_pct:.1f}%) flagged as sarcastic — consider manual review.')

    # Actionable insight
    if neg_pct > 30:
        lines.append(f'⚠️ {H}Action Required:{E} {neg:,} negative reviews detected — recommended for priority review.')
    elif pos_pct > 70:
        lines.append(f'✅ {H}Key Takeaway:{E} Strong positive sentiment indicates high customer satisfaction across the dataset.')

    return "<br>".join(lines)


def generate_summary_single(result: dict) -> str:
    """Generate AI micro-summary for a single review result.

    Returns clean HTML string — no markdown, structured format.
    """
    sentiment = result.get("sentiment", "Unknown")
    confidence = float(result.get("confidence", 0))
    polarity = float(result.get("polarity", 0))
    subjectivity = float(result.get("subjectivity", 0))

    conf_pct = confidence * 100 if confidence <= 1.0 else confidence
    conf_label = "high" if conf_pct > 75 else "moderate" if conf_pct > 55 else "low"
    pol_label = "positive" if polarity > 0.1 else "negative" if polarity < -0.1 else "balanced"
    subj_label = "highly subjective" if subjectivity > 0.6 else "objective" if subjectivity < 0.3 else "moderately subjective"

    H = '<span style="color:#00e5cc;font-weight:600;">'
    E = '</span>'
    lines = [
        f'📈 {H}Sentiment:{E} The review expresses a {sentiment.lower()} opinion with {conf_pct:.1f}% model confidence.',
        f'📐 {H}Polarity:{E} Score of {polarity:.3f} indicates a {pol_label} tone.',
        f'🎯 {H}Subjectivity:{E} At {subjectivity:.3f}, the text is {subj_label}.',
        f'💡 {H}Reliability:{E} Confidence level is {conf_label}, suggesting {"trustworthy" if conf_pct > 60 else "cautious"} interpretation.',
    ]

    sarcasm = result.get("sarcasm")
    if sarcasm and sarcasm.get("is_sarcastic"):
        lines.append(f'🎭 {H}Sarcasm:{E} Sarcasm detected — sentiment may not reflect true intent.')

    return "<br>".join(lines)


# ━━━ CHARTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_sentiment_pie(
    pos: int, neg: int, neu: int,
    positive_color: str, negative_color: str, neutral_color: str,
) -> go.Figure:
    """Build sentiment distribution donut chart."""
    fig = go.Figure(go.Pie(
        labels=["Positive", "Negative", "Neutral"],
        values=[pos, neg, neu],
        marker=dict(colors=[positive_color, negative_color, neutral_color]),
        hole=0.45,
        textinfo="label+percent",
    ))
    return fig


def build_keywords_chart(
    positive_kw: list[tuple[str, int]],
    negative_kw: list[tuple[str, int]],
    positive_color: str,
    negative_color: str,
) -> go.Figure:
    """Build horizontal bar chart for top keywords."""
    fig = go.Figure()
    if positive_kw:
        fig.add_trace(go.Bar(
            x=[c for _, c in positive_kw],
            y=[w for w, _ in positive_kw],
            orientation="h",
            marker_color=positive_color,
            name="Positive",
        ))
    if negative_kw:
        fig.add_trace(go.Bar(
            x=[c for _, c in negative_kw],
            y=[w for w, _ in negative_kw],
            orientation="h",
            marker_color=negative_color,
            name="Negative",
        ))
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return fig


def build_trend_chart(
    pos: int, neg: int, neu: int,
    positive_color: str, negative_color: str, neutral_color: str,
) -> go.Figure:
    """Build synthetic sentiment trend (6-month)."""
    months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
    bp = max(1, int(pos / 6))
    bn = max(1, int(neg / 6))
    bne = max(1, int(neu / 6))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=[max(1, bp + int(i * bp * 0.1)) for i in range(6)], mode="lines+markers", name="Positive", line=dict(color=positive_color, width=2.5)))
    fig.add_trace(go.Scatter(x=months, y=[max(1, bn - int(i * bn * 0.05)) for i in range(6)], mode="lines+markers", name="Negative", line=dict(color=negative_color, width=2.5)))
    fig.add_trace(go.Scatter(x=months, y=[max(1, bne - int(i * bne * 0.03)) for i in range(6)], mode="lines+markers", name="Neutral", line=dict(color=neutral_color, width=2.5)))
    return fig
