"""Live Sentiment Prediction — ReviewSense Analytics."""

import sys
import time
from pathlib import Path

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
from utils import load_model  # noqa: E402

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
# Text area + model/domain/stars all in ONE visual card

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

# ━━━ RESULTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if analyze_clicked:
    if not review_text.strip():
        st.warning("⚠️ Please enter some review text before analyzing.")
        st.stop()

    try:
        model_pipeline, label_map = load_model(selected_model)
    except Exception as e:
        st.error(f"Model loading error: {e}")
        st.stop()

    from src.predict import predict_sentiment  # noqa: E402

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

    result = predict_sentiment(review_text, model_pipeline)
    bar.progress(100)
    time.sleep(0.08)
    status_ph.empty()
    progress_ph.empty()

    pred_class = int(result["label"])
    label_name = LABEL_MAP[pred_class]
    confidence = float(result["confidence"])
    polarity = float(result["polarity"])
    subjectivity = float(result["subjectivity"])

    badge_class = {"Positive": "badge-positive", "Negative": "badge-negative", "Neutral": "badge-neutral"}.get(label_name, "badge-neutral")
    badge_display = {"Positive": "✅ Positive", "Negative": "❌ Negative", "Neutral": "◼ Neutral"}.get(label_name, label_name)

    # ── Results Header (Pattern A) ───────────────────────────
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
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── LIME (Pattern B) ─────────────────────────────────────
    with st.container():
        st.markdown("""
        <div class="glass-card-header">
          <div class="section-title">🔍 LIME Explanation</div>
          <div class="section-subtitle">Local Interpretable Model Explanations</div>
        </div>
        """, unsafe_allow_html=True)

        try:
            from src.lime_explainer import explain_prediction, highlight_text_html  # noqa: E402
            import plotly.graph_objects as go  # noqa: E402

            word_weights = explain_prediction(review_text, model_pipeline, num_features=10)
            highlighted = highlight_text_html(review_text, word_weights)
            st.markdown(highlighted, unsafe_allow_html=True)

            if word_weights:
                words = [w for w, _ in word_weights]
                weights = [v for _, v in word_weights]
                colors = [POSITIVE_COLOR if v >= 0 else NEGATIVE_COLOR for v in weights]
                fig = go.Figure(go.Bar(x=weights, y=words, orientation="h", marker_color=colors))
                apply_theme(fig, title="Top Feature Contributions", height=400, margin=dict(l=120))
                fig.update_layout(xaxis_title="← Negative | Positive →", yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig, use_container_width=True, key="lime_bar")
        except Exception as e:
            st.info(f"LIME explanation unavailable: {e}")

        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── ABSA (Pattern B) ─────────────────────────────────────
    with st.container():
        st.markdown("""
        <div class="glass-card-header">
          <div class="section-title">🔬 Aspect-Based Sentiment Analysis</div>
          <div class="section-subtitle">Token-level aspect extraction and polarity scoring</div>
        </div>
        """, unsafe_allow_html=True)

        try:
            from src.absa import get_aspect_dataframe  # noqa: E402
            import plotly.graph_objects as go  # noqa: E402
            aspect_df = get_aspect_dataframe(review_text)
            if aspect_df.empty:
                st.info("No distinct aspects detected in this review.")
            else:
                st.dataframe(aspect_df, use_container_width=True)
                colors = [POSITIVE_COLOR if p > 0.1 else NEGATIVE_COLOR if p < -0.1 else NEUTRAL_COLOR for p in aspect_df["Polarity"]]
                fig = go.Figure(go.Bar(x=aspect_df["Polarity"], y=aspect_df["Aspect"], orientation="h", marker_color=colors))
                apply_theme(fig, title="Aspect Polarity", height=max(300, len(aspect_df)*40), margin=dict(l=180))
                fig.update_layout(xaxis_title="Polarity", yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig, use_container_width=True, key="absa_bar")
        except Exception as e:
            st.info(f"Aspect analysis unavailable: {e}")

        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── Sarcasm + Gauge (2-col, each Pattern B) ──────────────
    sarc_col, gauge_col = st.columns(2)

    with sarc_col:
        with st.container():
            st.markdown('<div class="glass-card-header"><div class="section-title">🎭 Sarcasm Detection</div><div class="section-subtitle">Irony and sarcasm analysis</div></div>', unsafe_allow_html=True)
            try:
                from src.sarcasm_detector import detect_sarcasm  # noqa: E402
                sarc = detect_sarcasm(review_text, pred_class, star_val)
                if sarc["is_sarcastic"]:
                    st.markdown(f'<span class="tag-pill tag-amber" style="font-size:0.85rem;padding:6px 16px;">⚠️ SARCASM DETECTED</span><div style="margin-top:12px;color:#7986cb;font-size:0.9rem;"><strong>Reason:</strong> {sarc["reason"]}<br><strong>Irony Score:</strong> {sarc["confidence"]*100:.0f}%</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="tag-pill tag-green" style="font-size:0.85rem;padding:6px 16px;">✅ NO SARCASM</span><div style="margin-top:8px;color:#7986cb;font-size:0.9rem;">No sarcasm indicators detected.</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div style="color:#7986cb;">Sarcasm detection unavailable: {e}</div>', unsafe_allow_html=True)
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

    # ── Export (Pattern B) ───────────────────────────────────
    with st.container():
        st.markdown('<div class="glass-card-header"><div class="section-title">📥 Export Results</div><div class="section-subtitle">Download your analysis in multiple formats</div></div>', unsafe_allow_html=True)

        import json as _json  # noqa: E402
        _export_data = {"text": review_text, "sentiment": label_name, "confidence": round(confidence, 4), "polarity": round(polarity, 4), "subjectivity": round(subjectivity, 4)}
        e1, e2, e3 = st.columns(3)
        with e1:
            st.download_button("📊  Download CSV", data=f"text,sentiment,confidence,polarity,subjectivity\n\"{review_text}\",{label_name},{confidence:.4f},{polarity:.4f},{subjectivity:.4f}", file_name="reviewsense_result.csv", mime="text/csv", use_container_width=True, key="live_csv")
        with e2:
            st.download_button("📋  Download JSON", data=_json.dumps(_export_data, indent=2), file_name="reviewsense_result.json", mime="application/json", use_container_width=True, key="live_json")
        with e3:
            try:
                from src.pdf_exporter import export_report  # noqa: E402
                import tempfile, os  # noqa: E402
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as _tmp:
                    _tmp_path = _tmp.name
                try:
                    export_report({"single_result": _export_data}, _tmp_path)
                    with open(_tmp_path, "rb") as f: _pdf = f.read()
                    st.download_button("📄  Download PDF", data=_pdf, file_name="reviewsense_result.pdf", mime="application/pdf", use_container_width=True, key="live_pdf")
                finally:
                    if os.path.exists(_tmp_path): os.unlink(_tmp_path)
            except Exception:
                st.button("📄  Download PDF", disabled=True, use_container_width=True, key="live_pdf_dis")

        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)