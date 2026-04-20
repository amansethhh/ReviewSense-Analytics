"""Live Sentiment Prediction — ReviewSense Analytics.

Surfaces all pipeline signals: neutral correction, short-text guard,
temperature calibration, translation quality, Hinglish detection,
and sarcasm detection with progressive rendering (RT-2).
"""

import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import streamlit as st

_PAGE_DIR = Path(__file__).resolve().parent
_APP_DIR = _PAGE_DIR.parent
_PROJECT_ROOT = _APP_DIR.parent
for _p in (str(_PROJECT_ROOT), str(_APP_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

st.set_page_config(page_title="Live Prediction — ReviewSense", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

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
from ui.theme import apply_theme, POSITIVE_COLOR, NEGATIVE_COLOR, NEUTRAL_COLOR, ACCENT_BLUE  # noqa: E402
from src.config import DOMAINS, MODEL_NAMES, LABEL_MAP  # noqa: E402
from src.analytics import extract_keywords_single, generate_summary_single  # noqa: E402
from src.exporter import render_export_buttons  # noqa: E402


load_css()
render_sidebar()

# ━━━ PAGE HEADER (Pattern A) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div class="glass-card">
  <div class="section-title">⚡ Live Sentiment Prediction</div>
  <div class="section-subtitle" style="margin-bottom:0;">Real-time NLP analysis with confidence scoring, LIME explanations & aspect-level insights.</div>
</div>
""", unsafe_allow_html=True)

# ━━━ UNIFIED REVIEW INPUT CARD (Pattern B) ━━━━━━━━━━━━━━━━

with st.container():
    st.markdown("""
    <div class="glass-card-header">
      <div class="section-title">📝 Review Input</div>
      <div class="section-subtitle">Enter any review text in any language</div>
    </div>
    """, unsafe_allow_html=True)

    review_text = st.text_area(
        "Review Text", height=140,
        placeholder="The food was absolutely amazing but the service was incredibly slow and disappointing.",
        key="live_review", label_visibility="collapsed",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_model = st.selectbox("Model", ["best"] + MODEL_NAMES, index=0, key="pred_model")
    with col2:
        domain_context = st.selectbox("Domain Context", ["Auto-detect"] + DOMAINS, index=0, key="pred_domain")
    with col3:
        star_val = st.slider("Star Rating", 1, 5, 3, key="pred_stars")
        st.markdown(f"""
        <div style="font-size:1.1rem;letter-spacing:2px;margin-top:4px;">{"⭐" * star_val}</div>
        <div style="font-size:0.7rem;color:#7986cb;">{star_val} / 5 stars</div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━ ANALYZE BUTTON ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

analyze_clicked = st.button("⚡  Analyze Sentiment", use_container_width=True, key="live_analyze")

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━ SESSION STATE ━━━
for _ss_key, _ss_default in [
    ("live_result", None),
    ("live_review_analyzed", ""),
    ("live_lime_weights", None),
    ("live_lime_html", ""),
    ("live_absa_df", None),
]:
    if _ss_key not in st.session_state:
        st.session_state[_ss_key] = _ss_default

# ━━━ RESULTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if analyze_clicked:
    if not review_text.strip():
        st.warning("⚠️ Please enter some review text before analyzing.")
        st.stop()

    from src.pipeline.inference import run_pipeline, preload_models  # noqa: E402

    # Preload models eagerly (cached — instant on subsequent runs)
    preload_models()

    # ── Spinning ring + progress bar ─────────────────────────
    status_ph = st.empty()
    progress_ph = st.empty()
    status_ph.markdown("""
    <div class="analyze-loading">
      <div class="spin-ring"></div>
      <div>
        <div style="font-weight:600;color:#93c5fd;">Analyzing sentiment...</div>
        <div style="font-size:0.75rem;color:#7986cb;margin-top:2px;">Running NLP pipeline · LIME · ABSA</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    bar = progress_ph.progress(0)
    for pct in [10, 25, 45, 65, 80, 92]:
        time.sleep(0.1)
        bar.progress(pct)

    result = run_pipeline(review_text, enable_sarcasm=True, enable_aspects=True)
    bar.progress(100)
    time.sleep(0.08)
    status_ph.empty()
    progress_ph.empty()

    # RT-2: Eagerly compute LIME + ABSA and cache in session state
    _lime_weights = None
    _lime_html = ""
    try:
        from src.lime_explainer import explain_prediction, highlight_text_html  # noqa: E402
        _lime_weights = explain_prediction(review_text, num_features=6)
        _lime_html = highlight_text_html(review_text, _lime_weights)
    except Exception:
        pass

    _absa_df = None
    try:
        from src.absa import get_aspect_dataframe  # noqa: E402
        _absa_df = get_aspect_dataframe(review_text)
    except Exception:
        pass

    # Store ALL results in session state — survives rerenders
    st.session_state.live_result = result
    st.session_state.live_review_analyzed = review_text
    st.session_state.live_lime_weights = _lime_weights
    st.session_state.live_lime_html = _lime_html
    st.session_state.live_absa_df = _absa_df

# ━━━ RENDER FROM SESSION STATE (anti-flicker) ━━━

result = st.session_state.live_result
if result is None:
    st.stop()

review_text_display = st.session_state.live_review_analyzed

pred_class = int(result["label"])
label_name = LABEL_MAP.get(pred_class, result.get("sentiment", "Unknown"))
confidence = float(result["confidence"])
polarity = float(result["polarity"])
subjectivity = float(result["subjectivity"])

badge_class = {"Positive": "badge-positive", "Negative": "badge-negative", "Neutral": "badge-neutral"}.get(label_name, "badge-neutral")
badge_display = {"Positive": "✅ Positive", "Negative": "❌ Negative", "Neutral": "◼ Neutral"}.get(label_name, label_name)

# ── RT-2: Stage 1 — Core sentiment (fast) ────────────────
result_placeholder = st.empty()
with result_placeholder.container():
    st.markdown(f"""
    <div class="glass-card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
        <div class="section-title">📊 Analysis Results</div>
        <span class="{badge_class}" style="font-size:1.2rem;padding:8px 24px;">{badge_display}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 3-Column Metrics ─────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div class="metric-card metric-card-cyan"><div class="metric-label">CONFIDENCE SCORE</div><div class="metric-value">{confidence*100:.1f}%</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card metric-card-blue"><div class="metric-label">POLARITY</div><div class="metric-value">{polarity:.3f}</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card metric-card-violet"><div class="metric-label">SUBJECTIVITY</div><div class="metric-value">{subjectivity:.3f}</div></div>', unsafe_allow_html=True)

    st.progress(confidence, text=f"Confidence Level — {confidence*100:.1f}%")

    # ── ADD-ON 9: Pipeline signal indicators ─────────────────

    # Neutral correction indicator
    if result.get("neutral_corrected"):
        st.info("ℹ️ Confidence-adjusted to Neutral based on polarity analysis.")

    # Short-text guard indicator
    if result.get("guard_applied"):
        st.caption(f"ℹ️ Short-text guard applied: {result['guard_applied']}")

    # Temperature calibration transparency
    if result.get("temperature_scaled"):
        raw_pct = result.get("raw_confidence", confidence) * 100
        cal_pct = confidence * 100
        st.caption(f"ℹ️ Confidence calibrated: raw {raw_pct:.1f}% → calibrated {cal_pct:.1f}%")

    # Translation status badge
    translation_status = result.get("translation_status", "OK")
    if result.get("was_translated"):
        if translation_status == "OK":
            st.success("✓ Translation verified")
        elif translation_status == "RETRIED_OK":
            st.warning("⚠️ Translation required retry — verify result")
        elif translation_status == "FALLBACK_PASSTHROUGH":
            st.error("✗ Translation failed — original text used, result may be inaccurate")

    # Translation quality warning
    if result.get("translation_flagged"):
        st.warning("⚠️ Translation quality may be low. Result may be unreliable.")

    # View translation used
    if result.get("was_translated"):
        with st.expander("View translation used"):
            st.write(result.get("translated", ""))

    # Hinglish indicator
    if result.get("hinglish_detected"):
        st.info("🔤 Hinglish detected — direct multilingual inference used (no translation).")

    # Sarcasm override badge
    if result.get("sarcasm_applied"):
        st.warning("⚠️ Sarcasm detected — prediction flipped to Negative")

    # Uncertainty warning
    if result.get("uncertain_prediction"):
        st.caption(f"⚠️ Low confidence ({confidence*100:.1f}%) — result may be unreliable")

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── Keyword Extraction ─────────────────────────────
with st.container():
    st.markdown("""
    <div class="glass-card-header">
      <div class="section-title">🔑 Keyword Extraction</div>
      <div class="section-subtitle">Key terms detected in the review</div>
    </div>
    """, unsafe_allow_html=True)

    kw = extract_keywords_single(review_text_display, n=10)
    if kw:
        kw_html = " ".join(f'<span class="tag-pill tag-cyan" style="margin:2px;">{w} ({c})</span>' for w, c in kw)
        st.markdown(f'<div style="padding:8px 0;">{kw_html}</div>', unsafe_allow_html=True)
    else:
        st.info("No significant keywords detected.")

    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── AI Summary ─────────────────────────────────────
with st.container():
    st.markdown("""
    <div class="glass-card-header">
      <div class="section-title">🤖 AI Summary</div>
      <div class="section-subtitle">Single review insight</div>
    </div>
    """, unsafe_allow_html=True)

    summary_html = generate_summary_single(result)
    st.markdown(f'<div style="color:#e8eaf6;line-height:2.0;margin-bottom:12px;font-size:0.92rem;">{summary_html}</div>', unsafe_allow_html=True)
    st.markdown('<span class="tag-pill tag-violet">AI-GENERATED</span> <span class="tag-pill tag-cyan">INSTANT</span>', unsafe_allow_html=True)

    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── RT-2: Stage 2 — LIME (from session state — no recompute on rerun) ─────
with st.container():
    st.markdown("""
    <div class="glass-card-header">
      <div class="section-title">🔍 LIME Explanation</div>
      <div class="section-subtitle">Local Interpretable Model Explanations · Cached for speed</div>
    </div>
    """, unsafe_allow_html=True)

    word_weights = st.session_state.live_lime_weights
    lime_html = st.session_state.live_lime_html

    if lime_html:
        st.markdown(lime_html, unsafe_allow_html=True)

    if word_weights:
        import plotly.graph_objects as go  # noqa: E402
        words = [w for w, _ in word_weights]
        weights = [v for _, v in word_weights]
        colors = [POSITIVE_COLOR if v >= 0 else NEGATIVE_COLOR for v in weights]
        fig = go.Figure(go.Bar(x=weights, y=words, orientation="h", marker_color=colors))
        apply_theme(fig, title="Top Feature Contributions", height=350, margin=dict(l=120))
        fig.update_layout(xaxis_title="← Negative | Positive →", yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True, key="lime_bar")
    elif word_weights is None:
        st.info("LIME explanation unavailable for this text.")

    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── RT-2: Stage 3 — ABSA (from session state — no recompute on rerun) ────
with st.container():
    st.markdown("""
    <div class="glass-card-header">
      <div class="section-title">🔬 Aspect-Based Sentiment Analysis</div>
      <div class="section-subtitle">Token-level aspect extraction and polarity scoring</div>
    </div>
    """, unsafe_allow_html=True)

    aspect_df = st.session_state.live_absa_df
    if aspect_df is None or (hasattr(aspect_df, 'empty') and aspect_df.empty):
        st.info("No distinct aspects detected in this review.")
    else:
        import plotly.graph_objects as go  # noqa: E402
        st.dataframe(aspect_df, use_container_width=True)
        colors = [POSITIVE_COLOR if p > 0.1 else NEGATIVE_COLOR if p < -0.1 else NEUTRAL_COLOR for p in aspect_df["Polarity"]]
        fig = go.Figure(go.Bar(x=aspect_df["Polarity"], y=aspect_df["Aspect"], orientation="h", marker_color=colors))
        apply_theme(fig, title="Aspect Polarity", height=max(300, len(aspect_df)*40), margin=dict(l=180))
        fig.update_layout(xaxis_title="Polarity", yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True, key="absa_bar")

    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── RT-2: Stage 4 — Sarcasm + Gauge (2-col) ──────────────
sarc_col, gauge_col = st.columns(2)

with sarc_col:
    with st.container():
        st.markdown('<div class="glass-card-header"><div class="section-title">🎭 Sarcasm Detection</div><div class="section-subtitle">RoBERTa irony classifier</div></div>', unsafe_allow_html=True)
        sarc = result.get("sarcasm")
        if sarc and sarc.get("is_sarcastic"):
            st.markdown(f'<span class="tag-pill tag-amber" style="font-size:0.85rem;padding:6px 16px;">⚠️ SARCASM DETECTED</span><div style="margin-top:12px;color:#7986cb;font-size:0.9rem;"><strong>Reason:</strong> {sarc["reason"]}<br><strong>Irony Score:</strong> {sarc["confidence"]*100:.0f}%</div>', unsafe_allow_html=True)
        elif sarc:
            st.markdown(f'<span class="tag-pill tag-green" style="font-size:0.85rem;padding:6px 16px;">✅ NO SARCASM</span><div style="margin-top:8px;color:#7986cb;font-size:0.9rem;">{sarc["reason"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#7986cb;">Sarcasm analysis was not enabled.</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

with gauge_col:
    import plotly.graph_objects as go  # noqa: E402
    with st.container():
        st.markdown('<div class="glass-card-header"><div class="section-title">📈 Polarity Gauge</div><div class="section-subtitle">Visual polarity scale</div></div>', unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=polarity, title={"text": "Polarity Score"},
            gauge={"axis": {"range": [-1, 1]}, "bar": {"color": ACCENT_BLUE},
                "steps": [{"range": [-1, -0.3], "color": "rgba(239,68,68,0.15)"}, {"range": [-0.3, 0.3], "color": "rgba(156,163,175,0.15)"}, {"range": [0.3, 1], "color": "rgba(34,197,94,0.15)"}]}))
        apply_theme(fig_gauge, height=280, margin=dict(t=60, b=20, l=20, r=20))
        st.plotly_chart(fig_gauge, use_container_width=True, key="polarity_gauge")
        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── Export (centralized, 4-format) ─────
import pandas as pd  # noqa: E402
_export_df = pd.DataFrame([{
    "Text": review_text_display,
    "Sentiment": label_name,
    "Confidence": round(confidence, 4),
    "Polarity": round(polarity, 4),
    "Subjectivity": round(subjectivity, 4),
    "Neutral Corrected": result.get("neutral_corrected", False),
    "Guard Applied": result.get("guard_applied", ""),
    "Sarcasm": "Yes" if result.get("sarcasm", {}).get("is_sarcastic") else "No",
}])
render_export_buttons(_export_df, filename_prefix="reviewsense_live")