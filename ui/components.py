"""Reusable UI components for ReviewSense Analytics.

Every page imports these helpers so the UI stays consistent.
"""

from __future__ import annotations
import streamlit as st


# ──────────────────────────────────────────────────────────────
# Glass Card
# ──────────────────────────────────────────────────────────────

def glass_card(content: str, icon: str = "", extra_style: str = ""):
    """Render a glass-morphism card with raw HTML *content*."""
    header = f"<span style='font-size:1.15rem;margin-right:0.4rem;'>{icon}</span>" if icon else ""
    st.markdown(
        f"<div class='glass-card' style='{extra_style}'>{header}{content}</div>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────
# Metric Card (HTML version for colored top borders)
# ──────────────────────────────────────────────────────────────

def metric_card(label: str, value, delta: str = "", color: str = "#3b82f6"):
    """A single KPI metric rendered as an HTML glass card."""
    delta_html = ""
    if delta:
        delta_color = "#22c55e" if not delta.startswith("-") else "#ef4444"
        delta_html = f"<div style='font-size:0.75rem;color:{delta_color};font-weight:600;margin-top:0.2rem;'>{delta}</div>"
    st.markdown(
        f"""<div class='glass-card' style='border-top:3px solid {color};padding:1.15rem 1.25rem;'>
        <div style='color:#64748b;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;'>{label}</div>
        <div style='font-size:1.8rem;font-weight:700;color:#f1f5f9;margin-top:0.25rem;'>{value}</div>
        {delta_html}
        </div>""",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────
# Section Title
# ──────────────────────────────────────────────────────────────

def section_title(title: str, subtitle: str = "", icon: str = ""):
    """Consistent section header used across all pages."""
    prefix = f"{icon} " if icon else ""
    st.markdown(f"### {prefix}{title}")
    if subtitle:
        st.markdown(
            f"<p style='color:#94a3b8;margin-top:-0.6rem;font-size:0.9rem;'>{subtitle}</p>",
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────
# Page Header
# ──────────────────────────────────────────────────────────────

def page_header(icon: str, title: str, subtitle: str = ""):
    """Standard page title + description shown at the top of every page."""
    st.markdown(
        f"<h1 style='margin-bottom:0.1rem;'>{icon} {title}</h1>",
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f"<p style='color:#94a3b8;font-size:1.05rem;margin-top:0;'>{subtitle}</p>",
            unsafe_allow_html=True,
        )
    st.markdown("---")


# ──────────────────────────────────────────────────────────────
# Sentiment Badge
# ──────────────────────────────────────────────────────────────

def sentiment_badge(label_name: str):
    """Coloured pill badge for Positive / Negative / Neutral."""
    mapping = {
        "Positive": ("badge-positive", "✅ Positive"),
        "Negative": ("badge-negative", "❌ Negative"),
        "Neutral":  ("badge-neutral",  "◼ Neutral"),
    }
    css_class, display = mapping.get(label_name, ("badge-neutral", f"◼ {label_name}"))
    st.markdown(
        f"<span class='{css_class}' style='font-size:1.3rem;padding:0.5rem 1.5rem;'>{display}</span>",
        unsafe_allow_html=True,
    )


def sentiment_badge_html(label_name: str) -> str:
    """Return the sentiment badge as raw HTML string (for embedding)."""
    mapping = {
        "Positive": ("badge-positive", "✅ Positive"),
        "Negative": ("badge-negative", "❌ Negative"),
        "Neutral":  ("badge-neutral",  "◼ Neutral"),
    }
    css_class, display = mapping.get(label_name, ("badge-neutral", f"◼ {label_name}"))
    return f"<span class='{css_class}' style='font-size:1.3rem;padding:0.5rem 1.5rem;'>{display}</span>"


# ──────────────────────────────────────────────────────────────
# Step Card
# ──────────────────────────────────────────────────────────────

def step_card(number: int, text: str):
    """A numbered instruction step with a gradient circle."""
    st.markdown(
        f"""<div class='step-card'>
        <div class='step-number'>{number:02d}</div>
        <div style='color:#94a3b8;font-size:0.85rem;line-height:1.5;'>{text}</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────
# Language Card
# ──────────────────────────────────────────────────────────────

def language_card(flag: str, name: str, code: str):
    """Compact card showing a supported language."""
    st.markdown(
        f"""<div class='lang-card'>
        <div style='font-size:1.6rem;'>{flag}</div>
        <div style='font-weight:600;font-size:0.95rem;margin-top:0.25rem;'>{name}</div>
        <div style='color:#64748b;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;'>{code}</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────
# Chart Container (wraps a plotly figure in a glass card)
# ──────────────────────────────────────────────────────────────

def chart_container(fig, use_container_width: bool = True):
    """Render a Plotly figure inside a styled container."""
    st.plotly_chart(fig, use_container_width=use_container_width)


# ──────────────────────────────────────────────────────────────
# Hero card (used for best model highlight etc.)
# ──────────────────────────────────────────────────────────────

def hero_card(content: str):
    """A special gradient-tinted card for hero sections."""
    st.markdown(f"<div class='hero-card'>{content}</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Accent badge (small colored label)
# ──────────────────────────────────────────────────────────────

def accent_badge(text: str):
    """Gradient accent badge (e.g. 'BEST PERFORMING MODEL')."""
    st.markdown(f"<span class='accent-badge'>{text}</span>", unsafe_allow_html=True)
