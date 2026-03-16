"""ReviewSense Analytics — Home Page."""

import sys
from pathlib import Path

import streamlit as st

# ── Path bootstrap ───────────────────────────────────────────
_APP_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _APP_DIR.parent
for _p in (str(_PROJECT_ROOT), str(_APP_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Page config (must be first Streamlit call) ───────────────
st.set_page_config(
    page_title="ReviewSense Analytics",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── UI imports ───────────────────────────────────────────────
from ui.sidebar import load_css, render_sidebar  # noqa: E402
from ui.components import (                       # noqa: E402
    glass_card, metric_card, section_title, page_header,
)

load_css()
render_sidebar()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HERO — Animated Title
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown(
    """
    <div style="margin-bottom:0.3rem;">
        <span class="accent-badge">⚡ AI-Powered Sentiment Engine</span>
    </div>
    <div class="animated-title" style="margin-bottom:0.15rem;">ReviewSense Analytics</div>
    <p style="color:#94a3b8;font-size:1.1rem;max-width:680px;line-height:1.6;margin-top:0.25rem;">
        Harness the power of transformer-based NLP models to decode customer sentiment at scale.
        Real-time predictions, multi-language support, and domain-specific fine-tuning — all in one platform.
    </p>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KEY PERFORMANCE INDICATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

section_title("Key Performance Indicators", icon="📈")

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_card("Total Reviews Analyzed", "1.2M+", delta="↑ 23.5%", color="#3b82f6")
with k2:
    metric_card("Model Accuracy", "94.7%", delta="↑ 2.1%", color="#22c55e")
with k3:
    metric_card("Avg. Latency", "42ms", delta="↓ 15.3%", color="#06b6d4")
with k4:
    metric_card("Positive Sentiment", "78.2%", delta="↑ 5.8%", color="#7c3aed")

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORE CAPABILITIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

section_title("Core Capabilities", icon="🚀")

f1, f2, f3 = st.columns(3)

with f1:
    glass_card(
        """
        <h3 style='font-size:1.05rem;margin-bottom:0.5rem;'>⚡ Real-Time Prediction</h3>
        <p style='color:#94a3b8;font-size:0.88rem;line-height:1.6;'>
        Instant sentiment classification with confidence scoring. Type or paste any review
        and get immediate AI-powered analysis with LIME explanations.
        </p>
        <div style='margin-top:0.75rem;display:flex;gap:0.4rem;flex-wrap:wrap;'>
            <span style='background:rgba(59,130,246,0.12);color:#3b82f6;padding:0.2rem 0.6rem;border-radius:999px;font-size:0.7rem;font-weight:600;'>LIVE</span>
            <span style='background:rgba(6,182,212,0.12);color:#06b6d4;padding:0.2rem 0.6rem;border-radius:999px;font-size:0.7rem;font-weight:600;'>LOW LATENCY</span>
        </div>
        """
    )

with f2:
    glass_card(
        """
        <h3 style='font-size:1.05rem;margin-bottom:0.5rem;'>📂 Bulk Analysis</h3>
        <p style='color:#94a3b8;font-size:0.88rem;line-height:1.6;'>
        Upload CSV datasets with thousands of reviews. Automated batch processing with
        sentiment distribution charts, keyword analysis, and downloadable reports.
        </p>
        <div style='margin-top:0.75rem;display:flex;gap:0.4rem;flex-wrap:wrap;'>
            <span style='background:rgba(34,197,94,0.12);color:#22c55e;padding:0.2rem 0.6rem;border-radius:999px;font-size:0.7rem;font-weight:600;'>CSV UPLOAD</span>
            <span style='background:rgba(124,58,237,0.12);color:#7c3aed;padding:0.2rem 0.6rem;border-radius:999px;font-size:0.7rem;font-weight:600;'>BATCH</span>
        </div>
        """
    )

with f3:
    glass_card(
        """
        <h3 style='font-size:1.05rem;margin-bottom:0.5rem;'>🌐 Multi-Language Support</h3>
        <p style='color:#94a3b8;font-size:0.88rem;line-height:1.6;'>
        Analyze reviews in 50+ languages with automatic language detection and cross-lingual
        transfer learning capabilities. Seamless multilingual pipeline.
        </p>
        <div style='margin-top:0.75rem;display:flex;gap:0.4rem;flex-wrap:wrap;'>
            <span style='background:rgba(245,158,11,0.12);color:#f59e0b;padding:0.2rem 0.6rem;border-radius:999px;font-size:0.7rem;font-weight:600;'>50+ LANGUAGES</span>
            <span style='background:rgba(6,182,212,0.12);color:#06b6d4;padding:0.2rem 0.6rem;border-radius:999px;font-size:0.7rem;font-weight:600;'>AUTO-DETECT</span>
        </div>
        """
    )

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# QUICK ACTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

section_title("Quick Actions", icon="🎯")

q1, q2, q3 = st.columns(3)

with q1:
    if st.button("⚡  Try Live Prediction", use_container_width=True, key="qa_live"):
        st.switch_page("pages/01_Live_Prediction.py")

with q2:
    if st.button("📂  Upload Dataset", use_container_width=True, key="qa_bulk"):
        st.switch_page("pages/02_Bulk_Analysis.py")

with q3:
    if st.button("📊  View Model Dashboard", use_container_width=True, key="qa_dash"):
        st.switch_page("pages/03_Model_Dashboard.py")