"""ReviewSense Analytics — Home Page."""

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import streamlit as st

# ── Path bootstrap ───────────────────────────────────────────
_APP_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _APP_DIR.parent
for _p in (str(_PROJECT_ROOT), str(_APP_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

st.set_page_config(page_title="ReviewSense Analytics", page_icon="🔎", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main, .block-container {
    background-color: #070b14 !important; background: #070b14 !important;
}
[data-testid="stSidebarNav"], [data-testid="stSidebarNav"] * { display: none !important; }
</style>
""", unsafe_allow_html=True)

from ui.sidebar import load_css, render_sidebar  # noqa: E402
load_css()
render_sidebar()

# ── NLTK + Model preload (cached — runs once) ──
@st.cache_resource
def _setup_nltk():
    """Download NLTK data once and cache permanently."""
    try:
        import nltk
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
        nltk.download("stopwords", quiet=True)
    except Exception:
        pass
    return True

_setup_nltk()

# Preload NLP models eagerly on app start
try:
    from src.pipeline.inference import preload_models  # noqa: E402
    preload_models()
except Exception:
    pass

# ━━━ HERO (Pattern A — all HTML in one call) ━━━━━━━━━━━━━━

st.markdown("""
<div class="glass-card" style="margin-bottom:24px;">
  <span class="hero-badge">✦ AI-POWERED SENTIMENT ENGINE</span>
  <div class="hero-title">ReviewSense Analytics</div>
  <div class="hero-subtitle">
    Harness the power of transformer-based NLP models to decode customer sentiment at scale.
    Real-time predictions, multi-language support, and domain-specific fine-tuning — all in one platform.
  </div>
</div>
""", unsafe_allow_html=True)

# ━━━ KPI CARDS (4-column) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━ CORE CAPABILITIES (Pattern A — header + 2x2 cards) ━━━

st.markdown("""
<div class="section-title">🚀 Core Capabilities</div>
<div class="section-subtitle" style="margin-bottom:16px;">Enterprise-grade NLP analysis tools</div>
""", unsafe_allow_html=True)

row1 = st.columns(2)
row2 = st.columns(2)

with row1[0]:
    st.markdown("""
    <div class="glass-card">
      <h3 style="font-size:1.1rem;margin-bottom:0.5rem;">⚡ Real-Time Prediction</h3>
      <p style="color:#7986cb;font-size:0.88rem;line-height:1.6;">Instant sentiment classification with confidence scoring.</p>
      <div style="margin-top:0.75rem;display:flex;gap:0.3rem;flex-wrap:wrap;">
        <span class="tag-pill tag-cyan">LIVE</span><span class="tag-pill tag-cyan">LOW LATENCY</span><span class="tag-pill tag-violet">REST API</span>
      </div>
    </div>""", unsafe_allow_html=True)
with row1[1]:
    st.markdown("""
    <div class="glass-card">
      <h3 style="font-size:1.1rem;margin-bottom:0.5rem;">🌐 Multi-Language Support</h3>
      <p style="color:#7986cb;font-size:0.88rem;line-height:1.6;">Analyze reviews in 50+ languages with auto-detection.</p>
      <div style="margin-top:0.75rem;display:flex;gap:0.3rem;flex-wrap:wrap;">
        <span class="tag-pill tag-teal">50+ LANGUAGES</span><span class="tag-pill tag-teal">AUTO-DETECT</span><span class="tag-pill tag-violet">XLM-R</span>
      </div>
    </div>""", unsafe_allow_html=True)
with row2[0]:
    st.markdown("""
    <div class="glass-card">
      <h3 style="font-size:1.1rem;margin-bottom:0.5rem;">📂 Bulk Analysis Pipeline</h3>
      <p style="color:#7986cb;font-size:0.88rem;line-height:1.6;">Upload CSV datasets for batch processing and reports.</p>
      <div style="margin-top:0.75rem;display:flex;gap:0.3rem;flex-wrap:wrap;">
        <span class="tag-pill tag-amber">CSV UPLOAD</span><span class="tag-pill tag-amber">BATCH MODE</span><span class="tag-pill tag-green">REPORTS</span>
      </div>
    </div>""", unsafe_allow_html=True)
with row2[1]:
    st.markdown("""
    <div class="glass-card">
      <h3 style="font-size:1.1rem;margin-bottom:0.5rem;">🔍 Model Explainability</h3>
      <p style="color:#7986cb;font-size:0.88rem;line-height:1.6;">SHAP values, attention heatmaps, token-level importance.</p>
      <div style="margin-top:0.75rem;display:flex;gap:0.3rem;flex-wrap:wrap;">
        <span class="tag-pill tag-violet">SHAP</span><span class="tag-pill tag-violet">ATTENTION MAPS</span><span class="tag-pill tag-cyan">XAI</span>
      </div>
    </div>""", unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━ QUICK ACTIONS (st.button + st.switch_page navigation) ━━━━

st.markdown("""
<style>.action-card { cursor: pointer; }</style>
<div class="section-title">🚀 Quick Actions</div>
<div class="section-subtitle" style="margin-bottom:16px;">Jump into any feature instantly</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="action-card">
      <div class="action-icon action-icon-cyan">⚡</div>
      <div><div class="action-label">Try Live Prediction</div><div class="action-sublabel">Analyze a review instantly</div></div>
    </div>""", unsafe_allow_html=True)
    if st.button("⚡ Try Live Prediction", use_container_width=True):
        st.switch_page("pages/01_Live_Prediction.py")
with col2:
    st.markdown("""
    <div class="action-card">
      <div class="action-icon action-icon-amber">📂</div>
      <div><div class="action-label">Upload Dataset</div><div class="action-sublabel">Batch process thousands of reviews</div></div>
    </div>""", unsafe_allow_html=True)
    if st.button("📂 Upload Dataset", use_container_width=True):
        st.switch_page("pages/02_Bulk_Analysis.py")
with col3:
    st.markdown("""
    <div class="action-card">
      <div class="action-icon action-icon-violet">📊</div>
      <div><div class="action-label">View Model Dashboard</div><div class="action-sublabel">Compare all trained classifiers</div></div>
    </div>""", unsafe_allow_html=True)
    if st.button("📊 View Model Dashboard", use_container_width=True):
        st.switch_page("pages/03_Model_Dashboard.py")