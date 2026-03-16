"""Live Sentiment Prediction page for ReviewSense Analytics."""

import sys
from pathlib import Path
import streamlit as st

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_PAGE_DIR = Path(__file__).resolve().parent
_APP_DIR = _PAGE_DIR.parent
_PROJECT_ROOT = _APP_DIR.parent

for _p in (str(_PROJECT_ROOT), str(_APP_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Live Prediction — ReviewSense",
    layout="wide",
    page_icon="🎯",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from utils import load_css, render_sidebar, sentiment_badge_html
from src.config import DOMAINS, MODEL_NAMES, LABEL_MAP
from utils import load_model

# ---------------------------------------------------------------------------
# CSS + Sidebar
# ---------------------------------------------------------------------------
load_css()
sidebar_opts = render_sidebar()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("<h1>🎯 Live Sentiment Prediction</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#9e9eb8;'>Paste any product review and get an instant "
    "AI-powered sentiment analysis with word-level explanations.</p>",
    unsafe_allow_html=True,
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Input Section
# ---------------------------------------------------------------------------
review_text = st.text_area(
    "📝 Review Text",
    placeholder="Paste any product review here…",
    height=140,
)

c1, c2, c3 = st.columns(3)

with c1:
    selected_model = st.selectbox(
        "🤖 Model",
        ["best"] + MODEL_NAMES,
        index=0,
    )

with c2:
    domain_context = st.selectbox(
        "🏷️ Domain Context",
        ["Auto-detect"] + DOMAINS,
        index=0,
    )

with c3:
    star_rating = st.select_slider(
        "⭐ Star Rating (optional)",
        options=["—", 1, 2, 3, 4, 5],
        value="—",
    )

st.markdown("<br>", unsafe_allow_html=True)

analyze_clicked = st.button("⚡ Analyze Sentiment", use_container_width=True)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if analyze_clicked:

    if not review_text.strip():
        st.warning("⚠️ Please enter some review text before analyzing.")
        st.stop()

    try:
        model_pipeline, label_map = load_model(selected_model)
    except Exception as e:
        st.error(f"Model loading error: {e}")
        st.stop()

    from src.predict import predict_sentiment

    with st.spinner("Analyzing sentiment..."):
        result = predict_sentiment(review_text, model_pipeline)

    # ------------------------------------------------------------
    # SAFE LABEL MAPPING FIX
    # ------------------------------------------------------------
    pred_class = int(result["label"])  # numeric prediction
    label_name = LABEL_MAP[pred_class]

    confidence = float(result["confidence"])
    polarity = float(result["polarity"])
    subjectivity = float(result["subjectivity"])

    # -------------------------------------------------------------------
    # Result Header
    # -------------------------------------------------------------------
    st.markdown("## 📊 Results")

    badge_col, _ = st.columns([2, 5])

    with badge_col:
        st.markdown(sentiment_badge_html(label_name), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)

    m1.metric("🎯 Confidence", f"{confidence*100:.1f}%")
    m2.metric("📈 Polarity Score", f"{polarity:.3f}")
    m3.metric("💭 Subjectivity", f"{subjectivity:.3f}")

    st.progress(confidence, text=f"Model confidence: {confidence*100:.1f}%")

    st.markdown("---")

    # -------------------------------------------------------------------
    # LIME Explanation
    # -------------------------------------------------------------------
    st.markdown("## 🔍 LIME Explanation")

    try:
        from src.lime_explainer import explain_prediction, highlight_text_html
        import plotly.graph_objects as go

        word_weights = explain_prediction(review_text, model_pipeline, num_features=10)

        highlighted_html = highlight_text_html(review_text, word_weights)

        st.markdown(
            "**Highlighted text (green = supports prediction, red = opposes):**"
        )

        st.markdown(highlighted_html, unsafe_allow_html=True)

        if word_weights:

            words = [w for w, _ in word_weights]
            weights = [v for _, v in word_weights]

            colors = ["#00c851" if v >= 0 else "#ff4b4b" for v in weights]

            fig = go.Figure(
                go.Bar(
                    x=weights,
                    y=words,
                    orientation="h",
                    marker_color=colors,
                )
            )

            fig.update_layout(
                template="plotly_dark",
                title="Top Feature Contributions",
                xaxis_title="Weight",
                yaxis=dict(autorange="reversed"),
                height=400,
                margin=dict(l=120),
            )

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.info(f"LIME explanation unavailable: {e}")

    st.markdown("---")

    # -------------------------------------------------------------------
    # Aspect Analysis
    # -------------------------------------------------------------------
    st.markdown("## 🔎 Aspect-Based Sentiment Analysis")

    try:
        from src.absa import get_aspect_dataframe
        import plotly.graph_objects as go

        aspect_df = get_aspect_dataframe(review_text)

        if aspect_df.empty:
            st.info("No distinct aspects detected in this review.")
        else:
            st.dataframe(aspect_df, use_container_width=True)

            colors = [
                "#00c851" if p > 0.1 else "#ff4b4b" if p < -0.1 else "#ffa500"
                for p in aspect_df["Polarity"]
            ]

            fig = go.Figure(
                go.Bar(
                    x=aspect_df["Polarity"],
                    y=aspect_df["Aspect"],
                    orientation="h",
                    marker_color=colors,
                )
            )

            fig.update_layout(
                template="plotly_dark",
                title="Aspect Polarity",
                xaxis_title="Polarity",
                yaxis=dict(autorange="reversed"),
                height=max(300, len(aspect_df) * 40),
                margin=dict(l=180),
            )

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.info(f"Aspect analysis unavailable: {e}")

    st.markdown("---")

    # -------------------------------------------------------------------
    # Sarcasm Detection
    # -------------------------------------------------------------------
    st.markdown("## 🎭 Sarcasm Detection")

    try:
        from src.sarcasm_detector import detect_sarcasm

        star_val = None if star_rating == "—" else int(star_rating)

        sarc = detect_sarcasm(review_text, pred_class, star_val)

        if sarc["is_sarcastic"]:
            st.warning(
                f"Possible sarcasm detected\n\n"
                f"Reason: {sarc['reason']}\n\n"
                f"Confidence: {sarc['confidence']*100:.0f}%"
            )
        else:
            st.success("No sarcasm indicators detected.")

    except Exception as e:
        st.info(f"Sarcasm detection unavailable: {e}")