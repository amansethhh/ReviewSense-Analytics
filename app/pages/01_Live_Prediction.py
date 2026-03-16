"""Live Sentiment Prediction — ReviewSense Analytics."""

import sys
from pathlib import Path

import streamlit as st

# ── Path bootstrap ───────────────────────────────────────────
_PAGE_DIR = Path(__file__).resolve().parent
_APP_DIR = _PAGE_DIR.parent
_PROJECT_ROOT = _APP_DIR.parent
for _p in (str(_PROJECT_ROOT), str(_APP_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Live Prediction — ReviewSense",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── UI imports ───────────────────────────────────────────────
from ui.sidebar import load_css, render_sidebar          # noqa: E402
from ui.components import (                               # noqa: E402
    page_header, section_title, glass_card,
    sentiment_badge, sentiment_badge_html,
)
from ui.theme import (                                    # noqa: E402
    apply_theme, POSITIVE_COLOR, NEGATIVE_COLOR,
    NEUTRAL_COLOR, ACCENT_BLUE,
)
from src.config import DOMAINS, MODEL_NAMES, LABEL_MAP   # noqa: E402
from utils import load_model                          # noqa: E402

load_css()
render_sidebar()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

page_header(
    "⚡",
    "Live Sentiment Prediction",
    "Real-time NLP analysis with confidence scoring, LIME explanations & aspect-level insights",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INPUT PANEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

section_title("Review Input", icon="✏️")

review_text = st.text_area(
    "Review Text",
    placeholder="The food was absolutely amazing but the service was incredibly slow and disappointing.",
    height=130,
    key="live_review",
)

# ── Controls Row (page-level — moved from sidebar) ──────────
c1, c2, c3 = st.columns(3)
with c1:
    selected_model = st.selectbox("Model", ["best"] + MODEL_NAMES, index=0, key="live_model")
with c2:
    domain_context = st.selectbox("Domain", ["Auto-detect"] + DOMAINS, index=0, key="live_domain")
with c3:
    star_rating = st.select_slider(
        "Star Rating ⭐",
        options=["—", 1, 2, 3, 4, 5],
        value="—",
        key="live_stars",
    )

st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

# ── Analyze Button ───────────────────────────────────────────
st.markdown("<div class='gradient-btn'>", unsafe_allow_html=True)
analyze_clicked = st.button("⚡  Analyze Sentiment", use_container_width=True, key="live_analyze")
st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if analyze_clicked:
    if not review_text.strip():
        st.warning("⚠️ Please enter some review text before analyzing.")
        st.stop()

    # ── Load model ───────────────────────────────────────────
    try:
        model_pipeline, label_map = load_model(selected_model)
    except Exception as e:
        st.error(f"Model loading error: {e}")
        st.stop()

    from src.predict import predict_sentiment  # noqa: E402

    with st.spinner("Analyzing sentiment…"):
        result = predict_sentiment(review_text, model_pipeline)

    pred_class = int(result["label"])
    label_name = LABEL_MAP[pred_class]
    confidence = float(result["confidence"])
    polarity   = float(result["polarity"])
    subjectivity = float(result["subjectivity"])

    # ── Result Header ────────────────────────────────────────
    st.markdown("---")
    section_title("Results", icon="📊")

    res_left, res_right = st.columns([3, 1])
    with res_right:
        sentiment_badge(label_name)

    m1, m2, m3 = st.columns(3)
    m1.metric("🎯 Confidence Score", f"{confidence*100:.1f}%")
    m2.metric("📈 Polarity", f"{polarity:.3f}")
    m3.metric("💭 Subjectivity", f"{subjectivity:.3f}")

    st.progress(confidence, text=f"Confidence Level — {confidence*100:.1f}%")

    # ── LIME Explanation ─────────────────────────────────────
    st.markdown("---")
    section_title("LIME Explanation", subtitle="Local Interpretable Model Explanations", icon="🔍")

    try:
        from src.lime_explainer import explain_prediction, highlight_text_html  # noqa: E402
        import plotly.graph_objects as go  # noqa: E402

        word_weights = explain_prediction(review_text, model_pipeline, num_features=10)
        highlighted = highlight_text_html(review_text, word_weights)

        st.markdown("**Highlighted text** *(green = supports prediction, red = opposes)*")
        st.markdown(highlighted, unsafe_allow_html=True)

        if word_weights:
            words   = [w for w, _ in word_weights]
            weights = [v for _, v in word_weights]
            colors  = [POSITIVE_COLOR if v >= 0 else NEGATIVE_COLOR for v in weights]

            fig = go.Figure(go.Bar(x=weights, y=words, orientation="h", marker_color=colors))
            apply_theme(fig, title="Top Feature Contributions", height=400, margin=dict(l=120))
            fig.update_layout(xaxis_title="Weight", yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.info(f"LIME explanation unavailable: {e}")

    # ── Aspect-Based Sentiment Analysis ──────────────────────
    st.markdown("---")
    section_title("Aspect-Based Sentiment Analysis", icon="🔎")

    try:
        from src.absa import get_aspect_dataframe  # noqa: E402
        import plotly.graph_objects as go  # noqa: E402

        aspect_df = get_aspect_dataframe(review_text)

        if aspect_df.empty:
            st.info("No distinct aspects detected in this review.")
        else:
            st.dataframe(aspect_df, use_container_width=True)

            colors = [
                POSITIVE_COLOR if p > 0.1 else NEGATIVE_COLOR if p < -0.1 else NEUTRAL_COLOR
                for p in aspect_df["Polarity"]
            ]
            fig = go.Figure(go.Bar(
                x=aspect_df["Polarity"], y=aspect_df["Aspect"],
                orientation="h", marker_color=colors,
            ))
            apply_theme(fig, title="Aspect Polarity", height=max(300, len(aspect_df) * 40),
                        margin=dict(l=180))
            fig.update_layout(xaxis_title="Polarity", yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.info(f"Aspect analysis unavailable: {e}")

    # ── Sarcasm Detection ────────────────────────────────────
    st.markdown("---")
    section_title("Sarcasm Detection", icon="🎭")

    try:
        from src.sarcasm_detector import detect_sarcasm  # noqa: E402

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

    # ── Export Options ────────────────────────────────────────
    st.markdown("---")
    section_title("Export Options", icon="📥")

    import json as _json  # noqa: E402, F811

    _export_data = {
        "text": review_text,
        "sentiment": label_name,
        "confidence": round(confidence, 4),
        "polarity": round(polarity, 4),
        "subjectivity": round(subjectivity, 4),
    }

    e1, e2, e3 = st.columns(3)
    with e1:
        st.download_button(
            "📊  Download CSV",
            data=f"text,sentiment,confidence,polarity,subjectivity\n"
                 f"\"{review_text}\",{label_name},{confidence:.4f},{polarity:.4f},{subjectivity:.4f}",
            file_name="reviewsense_result.csv", mime="text/csv",
            use_container_width=True, key="live_csv",
        )
    with e2:
        st.download_button(
            "📋  Download JSON",
            data=_json.dumps(_export_data, indent=2),
            file_name="reviewsense_result.json", mime="application/json",
            use_container_width=True, key="live_json",
        )
    with e3:
        try:
            from src.pdf_exporter import export_report  # noqa: E402
            import tempfile, os  # noqa: E402

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as _tmp:
                _tmp_path = _tmp.name
            try:
                export_report({"single_result": _export_data}, _tmp_path)
                with open(_tmp_path, "rb") as f:
                    _pdf = f.read()
                st.download_button(
                    "📄  Download PDF",
                    data=_pdf,
                    file_name="reviewsense_result.pdf", mime="application/pdf",
                    use_container_width=True, key="live_pdf",
                )
            finally:
                if os.path.exists(_tmp_path):
                    os.unlink(_tmp_path)
        except Exception:
            st.button("📄  Download PDF", disabled=True, use_container_width=True, key="live_pdf_dis")