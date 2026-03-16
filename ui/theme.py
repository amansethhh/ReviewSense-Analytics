"""Plotly chart theming for ReviewSense Analytics.

Every chart must use ``apply_theme(fig)`` before rendering to ensure
consistent dark-transparent styling.
"""

from __future__ import annotations

# ── Sentiment colours ──
POSITIVE_COLOR = "#22c55e"
NEGATIVE_COLOR = "#ef4444"
NEUTRAL_COLOR  = "#9ca3af"
ACCENT_BLUE    = "#3b82f6"
ACCENT_PURPLE  = "#7c3aed"
ACCENT_CYAN    = "#06b6d4"

# Palette for multi-series charts
CHART_PALETTE = [ACCENT_BLUE, POSITIVE_COLOR, "#f59e0b", NEGATIVE_COLOR, ACCENT_PURPLE, ACCENT_CYAN]

SENTIMENT_COLORS = {
    "Positive": POSITIVE_COLOR,
    "Negative": NEGATIVE_COLOR,
    "Neutral":  NEUTRAL_COLOR,
}


def get_plotly_layout(**overrides) -> dict:
    """Return a reusable Plotly ``update_layout`` kwargs dict.

    Pass any overrides (e.g. ``title``, ``height``) and they will merge
    on top of the defaults.
    """
    base = dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#e2e8f0"),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(255,255,255,0.06)",
            borderwidth=1,
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            zerolinecolor="rgba(255,255,255,0.06)",
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            zerolinecolor="rgba(255,255,255,0.06)",
        ),
    )
    base.update(overrides)
    return base


def apply_theme(fig, **overrides):
    """Apply the ReviewSense dark theme to any Plotly figure in-place."""
    fig.update_layout(**get_plotly_layout(**overrides))
    return fig
