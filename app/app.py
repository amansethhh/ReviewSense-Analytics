import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Path bootstrap – must happen before any local imports
# ---------------------------------------------------------------------------
_APP_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _APP_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ReviewSense Analytics",
    layout="wide",
    page_icon="🔍",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------
_CSS_PATH = _APP_DIR / "assets" / "style.css"
if _CSS_PATH.exists():
    st.markdown(f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
from app.utils import render_sidebar  # noqa: E402  (after sys.path setup)

sidebar_opts = render_sidebar()

# ---------------------------------------------------------------------------
# Home page content
# ---------------------------------------------------------------------------
st.markdown(
    "<h1 style='text-align:center;margin-bottom:0;'>🔍 ReviewSense Analytics</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;color:#9e9eb8;font-size:1.2rem;margin-top:0.25rem;'>"
    "AI-Powered Multi-Domain Sentiment Intelligence"
    "</p>",
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# ── Metric cards ──────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("📚 Reviews Trained", "1.3M+")
col2.metric("🎯 Accuracy", "90%+")
col3.metric("🗂️ Datasets", "12")
col4.metric("🧠 AI Features", "13")

st.markdown("<br>", unsafe_allow_html=True)

# ── What This System Does ─────────────────────────────────────────────────
st.markdown("## 🚀 What This System Does")
st.markdown("<br>", unsafe_allow_html=True)

feat_col1, feat_col2 = st.columns(2)

with feat_col1:
    with st.container():
        st.markdown(
            """<div class='rs-card'>
            <h3>⚡ Live Analysis</h3>
            <p style='color:#9e9eb8;'>Paste any product review and receive an instant
            sentiment prediction with LIME word-level explanations and aspect-level
            breakdown in under a second.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container():
        st.markdown(
            """<div class='rs-card'>
            <h3>🔬 ABSA</h3>
            <p style='color:#9e9eb8;'>Aspect-Based Sentiment Analysis extracts individual
            product features (battery, screen, delivery…) and scores each one separately
            using spaCy noun-chunk extraction and TextBlob polarity.</p>
            </div>""",
            unsafe_allow_html=True,
        )

with feat_col2:
    with st.container():
        st.markdown(
            """<div class='rs-card'>
            <h3>📂 Bulk Processing</h3>
            <p style='color:#9e9eb8;'>Upload a CSV of thousands of reviews, auto-detect
            the text column, run batch inference with a progress bar, and download a
            fully-annotated results file alongside an AI-generated summary.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container():
        st.markdown(
            """<div class='rs-card'>
            <h3>🔍 XAI Explainability</h3>
            <p style='color:#9e9eb8;'>Every prediction comes with a LIME explanation —
            highlighted words that pushed the model towards its decision, plus a
            ranked bar chart showing feature contributions.</p>
            </div>""",
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Quick demo ────────────────────────────────────────────────────────────
st.markdown("## 🎮 Quick Demo")

with st.container():
    demo_text = st.text_input(
        "Enter a short review to try the model:",
        placeholder="e.g. The battery life is amazing but the screen is too dim.",
        key="home_demo_text",
    )
    if st.button("⚡ Analyze Now", key="home_analyze_btn"):
        if not demo_text.strip():
            st.warning("Please enter some text to analyze.")
        else:
            try:
                from src.predict import load_model, predict_sentiment

                @st.cache_resource
                def _load_best_model():
                    return load_model("best")

                model_pipeline, _ = _load_best_model()
                result = predict_sentiment(demo_text, model_pipeline)
                label_name = result["label_name"]
                badge_map = {"Positive": "✅", "Negative": "❌", "Neutral": "🟡"}
                emoji = badge_map.get(label_name, "🟡")
                conf_pct = round(result["confidence"] * 100, 1)
                st.success(
                    f"{emoji} **{label_name}** — Confidence: **{conf_pct}%** | "
                    f"Polarity: **{result['polarity']:.3f}**"
                )
            except FileNotFoundError:
                st.info(
                    "💡 Model file not found. Train the model first using "
                    "`python src/train_classical.py`, then relaunch the app."
                )
            except Exception as exc:
                st.error(f"Prediction error: {exc}")