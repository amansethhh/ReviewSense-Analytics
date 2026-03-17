"""Sidebar module — Navigation + Model Configuration.

FIX 7: Correct order — Logo → System Online → Nav → Model Config → Footer (pinned)
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
    """Render sidebar with logo, status, navigation, model config, footer."""

    # 1. Kill native Streamlit nav
    st.markdown("""
    <style>
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNav"] * { display:none!important; }
    </style>
    """, unsafe_allow_html=True)

    # 2. Logo + branding
    st.sidebar.markdown("""
    <div style="padding:8px 0 12px 0; border-bottom:
      1px solid rgba(59,130,246,0.1); margin-bottom:0;">
      <div style="display:flex; align-items:center; gap:10px;">
        <div style="width:36px;height:36px;border-radius:10px;
          background:linear-gradient(135deg,#3b82f6,#7b2fff);
          display:flex;align-items:center;justify-content:center;
          font-size:1.1rem;">🔎</div>
        <div>
          <div style="font-weight:800;font-size:0.95rem;
            color:#e8eaf6;">ReviewSense</div>
          <div style="font-size:0.7rem;color:#7986cb;">
            AI Sentiment Intelligence</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. System Online badge (immediately below logo)
    st.sidebar.markdown("""
    <div style="padding:4px 0 16px 0;
      border-bottom:1px solid rgba(59,130,246,0.1);
      margin-bottom:16px;">
      <span style="color:#22c55e;font-size:0.75rem;
        font-weight:600;letter-spacing:0.3px;">
        ● All Systems Operational
      </span>
    </div>
    """, unsafe_allow_html=True)

    # 4. Navigation
    st.sidebar.markdown(
        '<p style="font-size:0.7rem;font-weight:700;'
        'letter-spacing:1px;color:#4a5568;'
        'text-transform:uppercase;margin-bottom:8px;">'
        'NAVIGATION</p>',
        unsafe_allow_html=True,
    )
    st.sidebar.page_link("app.py", label="🏠  Home")
    st.sidebar.page_link("pages/01_Live_Prediction.py", label="⚡  Live Prediction")
    st.sidebar.page_link("pages/02_Bulk_Analysis.py", label="📂  Bulk Analysis")
    st.sidebar.page_link("pages/03_Model_Dashboard.py", label="📊  Model Dashboard")
    st.sidebar.page_link("pages/04_Language_Analysis.py", label="🌐  Language Analysis")

    # 5. Model Configuration
    st.sidebar.markdown("""
    <div style="margin-top:24px;padding-top:16px;
      border-top:1px solid rgba(59,130,246,0.1);">
    <p style="font-size:0.7rem;font-weight:700;
      letter-spacing:1px;color:#4a5568;
      text-transform:uppercase;margin-bottom:12px;">
      ⚙️ MODEL CONFIGURATION</p>
    </div>
    """, unsafe_allow_html=True)

    selected_model = st.sidebar.selectbox(
        "Active Model",
        ["best", "LinearSVC", "Logistic Regression",
         "Naive Bayes", "Random Forest"],
        key="global_model",
    )
    confidence_threshold = st.sidebar.slider(
        "Confidence Threshold",
        0.0, 1.0, 0.75, 0.05,
        key="global_confidence",
    )
    domain_filter = st.sidebar.selectbox(
        "Domain Filter",
        ["All Domains", "Food & Dining", "E-Commerce",
         "Social Media", "Movie Reviews", "Product Reviews"],
        key="global_domain",
    )

    st.session_state["selected_model"] = selected_model
    st.session_state["confidence_threshold"] = confidence_threshold
    st.session_state["domain_filter"] = domain_filter

    # 6. Spacer — pushes footer to bottom via flex
    st.sidebar.markdown(
        '<div class="sidebar-footer-spacer"></div>',
        unsafe_allow_html=True,
    )

    # 7. Footer — pinned to bottom
    st.sidebar.markdown("""
    <div class="sidebar-footer">
      ReviewSense Analytics<br>
      AI Sentiment Intelligence Platform<br>
      © 2026
    </div>
    """, unsafe_allow_html=True)
