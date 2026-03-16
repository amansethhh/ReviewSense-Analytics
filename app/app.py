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

# ── PHASE 0: Inject background immediately (no white flash) ─
st.markdown("""
<style>
html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main, .block-container {
    background-color: #070b14 !important;
    background: #070b14 !important;
}
[data-testid="stSidebarNav"],
[data-testid="stSidebarNav"] * {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ── Load CSS + Sidebar ───────────────────────────────────────
from ui.sidebar import load_css, render_sidebar  # noqa: E402

load_css()
render_sidebar()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HERO — Typing Animation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_PHRASES = [
    "ReviewSense Analytics",
    "AI Sentiment Intelligence",
    "Customer Insight Engine",
]

if "hero_phrase_idx" not in st.session_state:
    st.session_state["hero_phrase_idx"] = 0

_current_phrase = _PHRASES[st.session_state["hero_phrase_idx"] % len(_PHRASES)]

st.markdown(
    '<span class="hero-badge">✦ AI-POWERED SENTIMENT ENGINE</span>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="hero-title">{_current_phrase}<span class="cursor-blink">|</span></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hero-subtitle">'
    "Harness the power of transformer-based NLP models to decode customer sentiment at scale. "
    "Real-time predictions, multi-language support, and domain-specific fine-tuning — all in one platform."
    "</div>",
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KPI CARDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_KPIs = [
    ("TOTAL REVIEWS ANALYZED", "1.2M+", "+23.5%", "positive", "cyan"),
    ("MODEL ACCURACY", "94.7%", "+2.1%", "positive", "green"),
    ("AVG. LATENCY", "42ms", "-15.3%", "positive", "teal"),
    ("POSITIVE SENTIMENT", "78.2%", "+5.8%", "positive", "violet"),
]

col1, col2, col3, col4 = st.columns(4)
for col, (label, value, delta, delta_type, color) in zip(
    [col1, col2, col3, col4], _KPIs
):
    delta_class = "metric-delta-positive" if delta_type == "positive" else "metric-delta-negative"
    with col:
        st.markdown(f"""
        <div class="metric-card metric-card-{color}">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="{delta_class}">{delta}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORE CAPABILITIES (2x2 Grid)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown(
    '<div class="section-title">🚀 Core Capabilities</div>'
    '<div class="section-subtitle">Enterprise-grade NLP analysis tools</div>',
    unsafe_allow_html=True,
)

row1 = st.columns(2)
row2 = st.columns(2)

with row1[0]:
    st.markdown("""
    <div class="glass-card">
      <h3 style="font-size:1.1rem;margin-bottom:0.5rem;">⚡ Real-Time Prediction</h3>
      <p style="color:#7986cb;font-size:0.88rem;line-height:1.6;">
        Instant sentiment classification with confidence scoring.
      </p>
      <div style="margin-top:0.75rem;display:flex;gap:0.3rem;flex-wrap:wrap;">
        <span class="tag-pill tag-cyan">LIVE</span>
        <span class="tag-pill tag-cyan">LOW LATENCY</span>
        <span class="tag-pill tag-violet">REST API</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

with row1[1]:
    st.markdown("""
    <div class="glass-card">
      <h3 style="font-size:1.1rem;margin-bottom:0.5rem;">🌐 Multi-Language Support</h3>
      <p style="color:#7986cb;font-size:0.88rem;line-height:1.6;">
        Analyze reviews in 50+ languages with auto-detection.
      </p>
      <div style="margin-top:0.75rem;display:flex;gap:0.3rem;flex-wrap:wrap;">
        <span class="tag-pill tag-teal">50+ LANGUAGES</span>
        <span class="tag-pill tag-teal">AUTO-DETECT</span>
        <span class="tag-pill tag-violet">XLM-R</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

with row2[0]:
    st.markdown("""
    <div class="glass-card">
      <h3 style="font-size:1.1rem;margin-bottom:0.5rem;">📂 Bulk Analysis Pipeline</h3>
      <p style="color:#7986cb;font-size:0.88rem;line-height:1.6;">
        Upload CSV datasets for batch processing and reports.
      </p>
      <div style="margin-top:0.75rem;display:flex;gap:0.3rem;flex-wrap:wrap;">
        <span class="tag-pill tag-amber">CSV UPLOAD</span>
        <span class="tag-pill tag-amber">BATCH MODE</span>
        <span class="tag-pill tag-green">REPORTS</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

with row2[1]:
    st.markdown("""
    <div class="glass-card">
      <h3 style="font-size:1.1rem;margin-bottom:0.5rem;">🔍 Model Explainability</h3>
      <p style="color:#7986cb;font-size:0.88rem;line-height:1.6;">
        SHAP values, attention heatmaps, token-level importance.
      </p>
      <div style="margin-top:0.75rem;display:flex;gap:0.3rem;flex-wrap:wrap;">
        <span class="tag-pill tag-violet">SHAP</span>
        <span class="tag-pill tag-violet">ATTENTION MAPS</span>
        <span class="tag-pill tag-cyan">XAI</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# QUICK ACTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown(
    '<div class="section-title">🎯 Quick Actions</div>'
    '<div class="section-subtitle">Jump into any feature instantly</div>',
    unsafe_allow_html=True,
)

q1, q2, q3 = st.columns(3)
with q1:
    st.page_link("pages/01_Live_Prediction.py", label="⚡ Try Live Prediction", use_container_width=True)
with q2:
    st.page_link("pages/02_Bulk_Analysis.py", label="📂 Upload Dataset", use_container_width=True)
with q3:
    st.page_link("pages/03_Model_Dashboard.py", label="📊 View Model Dashboard", use_container_width=True)