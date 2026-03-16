"""Sidebar module — navigation only.

This replaces the previous render_sidebar() from app/utils.py which
contained duplicate model/confidence/domain controls.
The sidebar now shows ONLY the logo and page links.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

_UI_DIR = Path(__file__).resolve().parent
_CSS_PATH = _UI_DIR / "styles.css"


def load_css():
    """Inject the global CSS theme into the Streamlit page."""
    if _CSS_PATH.exists():
        css_text = _CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css_text}</style>", unsafe_allow_html=True)


def render_sidebar():
    """Render a clean navigation-only sidebar.

    No model selector, confidence slider, or domain filter.
    Those controls now live inside each page.
    """
    with st.sidebar:
        # ── Logo ──
        st.markdown(
            "<div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.25rem;'>"
            "<div style='width:36px;height:36px;border-radius:10px;"
            "background:linear-gradient(135deg,#3b82f6,#7c3aed);"
            "display:flex;align-items:center;justify-content:center;"
            "font-size:1.1rem;'>🔎</div>"
            "<div>"
            "<div style='font-weight:700;font-size:1rem;color:#f1f5f9;line-height:1.2;'>ReviewSense</div>"
            "<div style='font-size:0.65rem;color:#64748b;letter-spacing:0.06em;text-transform:uppercase;'>Analytics</div>"
            "</div></div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ── Navigation ──
        st.markdown(
            "<div style='color:#64748b;font-size:0.7rem;text-transform:uppercase;"
            "letter-spacing:0.12em;font-weight:600;margin-bottom:0.5rem;'>Navigation</div>",
            unsafe_allow_html=True,
        )

        st.page_link("app.py",                              label="🏠  Home")
        st.page_link("pages/01_Live_Prediction.py",         label="⚡  Live Prediction")
        st.page_link("pages/02_Bulk_Analysis.py",           label="📂  Bulk Analysis")
        st.page_link("pages/03_Model_Dashboard.py",         label="📊  Model Dashboard")
        st.page_link("pages/04_Language_Analysis.py",       label="🌐  Language Analysis")

        st.markdown("---")

        # ── System status ──
        st.markdown(
            "<div style='display:flex;align-items:center;gap:0.5rem;margin-top:auto;'>"
            "<div style='width:8px;height:8px;border-radius:50%;background:#22c55e;'></div>"
            "<span style='font-size:0.75rem;color:#94a3b8;'>System Online</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
        st.caption("Group 19 — Thapar Institute")
