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
# CSS
# ---------------------------------------------------------------------------
_CSS_PATH = _APP_DIR / "assets" / "style.css"
if _CSS_PATH.exists():
    st.markdown(f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
from app.utils import render_sidebar, sentiment_badge_html  # noqa: E402

sidebar_opts = render_sidebar()

# ---------------------------------------------------------------------------
# Model loading (cached)
# ---------------------------------------------------------------------------
from src.config import DOMAINS, MODEL_NAMES  # noqa: E402


@st.cache_resource
def load_model(model_name: str = "best"):
    """Load model once and cache for the session lifetime."""
    from src.predict import load_model as _load
    return _load(model_name)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
with st.container():
    st.markdown("<h1>🎯 Live Sentiment Prediction</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#9e9eb8;'>Paste any product review and get an instant "
        "AI-powered sentiment analysis with word-level explanations.</p>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Input section
# ---------------------------------------------------------------------------
with st.container():
    review_text = st.text_area(
        "📝 Review Text",
        placeholder="Paste any product review here…",
        height=140,
        key="lp_review_text",
    )

    inp_col1, inp_col2, inp_col3 = st.columns(3)
    with inp_col1:
        selected_model = st.selectbox(
            "🤖 Model",
            ["best"] + MODEL_NAMES,
            index=0,
            key="lp_model",
        )
    with inp_col2:
        domain_context = st.selectbox(
            "🏷️ Domain Context",
            ["Auto-detect"] + DOMAINS,
            index=0,
            key="lp_domain",
        )
    with inp_col3:
        star_rating = st.select_slider(
            "⭐ Star Rating (optional)",
            options=["—", 1, 2, 3, 4, 5],
            value="—",
            key="lp_stars",
        )

st.markdown("<br>", unsafe_allow_html=True)

# Full-width analyze button
analyze_clicked = st.button(
    "⚡ Analyze Sentiment",
    use_container_width=True,
    key="lp_analyze_btn",
)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if analyze_clicked:
    if not review_text.strip():
        st.warning("⚠️ Please enter some review text before analyzing.")
        st.stop()

    # ── Load model ──────────────────────────────────────────────────────────
    try:
        model_pipeline, label_map = load_model(selected_model)
    except FileNotFoundError:
        st.error(
            "🚫 Model file not found. Train the model first:\n\n"
            "```\npython src/train_classical.py\n```"
        )
        st.stop()
    except Exception as exc:
        st.error(f"Model loading error: {exc}")
        st.stop()

    # ── Predict ─────────────────────────────────────────────────────────────
    from src.predict import predict_sentiment  # noqa: E402

    with st.spinner("Analyzing…"):
        star_val = None if star_rating == "—" else int(star_rating)
        result = predict_sentiment(review_text, model_pipeline)

    label_name = result["label_name"]
    confidence = result["confidence"]
    polarity = result["polarity"]
    subjectivity = result["subjectivity"]

    # ── Sentiment badge + metrics ────────────────────────────────────────────
    st.markdown("## 📊 Results")
    with st.container():
        badge_col, _ = st.columns([2, 5])
        with badge_col:
            st.markdown(sentiment_badge_html(label_name), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("🎯 Confidence", f"{confidence * 100:.1f}%")
        m2.metric("📈 Polarity Score", f"{polarity:.3f}")
        m3.metric("💭 Subjectivity", f"{subjectivity:.3f}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.progress(float(confidence), text=f"Model confidence: {confidence * 100:.1f}%")

    st.markdown("---")

    # ── LIME Explanation ─────────────────────────────────────────────────────
    st.markdown("## 🔍 LIME Explanation")
    with st.container():
        with st.spinner("Generating LIME explanation…"):
            try:
                from src.lime_explainer import explain_prediction, highlight_text_html  # noqa: E402

                word_weights = explain_prediction(review_text, model_pipeline, num_features=10)
                highlighted_html = highlight_text_html(review_text, word_weights)

                st.markdown("**Highlighted text** (green = supports prediction, red = opposes):")
                st.markdown(highlighted_html, unsafe_allow_html=True)

                if word_weights:
                    st.markdown("<br>", unsafe_allow_html=True)
                    import plotly.graph_objects as go  # noqa: E402

                    words = [w for w, _ in word_weights]
                    weights = [v for _, v in word_weights]
                    colors = ["#00c851" if v >= 0 else "#ff4b4b" for v in weights]

                    fig_lime = go.Figure(
                        go.Bar(
                            x=weights,
                            y=words,
                            orientation="h",
                            marker_color=colors,
                        )
                    )
                    fig_lime.update_layout(
                        template="plotly_dark",
                        title="Top Feature Contributions",
                        xaxis_title="Weight",
                        yaxis=dict(autorange="reversed"),
                        height=400,
                        margin=dict(l=120),
                    )
                    st.plotly_chart(fig_lime, use_container_width=True)
            except Exception as exc:
                st.info(f"LIME explanation unavailable: {exc}")

    st.markdown("---")

    # ── Aspect Analysis ─────────────────────────────────────────────────────
    st.markdown("## 🔎 Aspect-Based Sentiment Analysis")
    with st.container():
        try:
            from src.absa import get_aspect_dataframe  # noqa: E402
            import plotly.graph_objects as go  # noqa: E402

            aspect_df = get_aspect_dataframe(review_text)

            if aspect_df.empty:
                st.info("No distinct aspects detected in this review.")
            else:
                st.dataframe(aspect_df, use_container_width=True)

                colors_asp = [
                    "#00c851" if row["Polarity"] > 0.1
                    else ("#ff4b4b" if row["Polarity"] < -0.1 else "#ffa500")
                    for _, row in aspect_df.iterrows()
                ]
                fig_asp = go.Figure(
                    go.Bar(
                        x=aspect_df["Polarity"],
                        y=aspect_df["Aspect"],
                        orientation="h",
                        marker_color=colors_asp,
                    )
                )
                fig_asp.update_layout(
                    template="plotly_dark",
                    title="Aspect Polarity",
                    xaxis_title="Polarity",
                    yaxis=dict(autorange="reversed"),
                    height=max(300, len(aspect_df) * 40),
                    margin=dict(l=180),
                )
                st.plotly_chart(fig_asp, use_container_width=True)
        except Exception as exc:
            st.info(f"Aspect analysis unavailable: {exc}")

    st.markdown("---")

    # ── Additional Analysis ──────────────────────────────────────────────────
    st.markdown("## 🧩 Additional Analysis")
    add_col1, add_col2 = st.columns(2)

    with add_col1:
        st.markdown("### 🎭 Sarcasm Detection")
        try:
            from src.sarcasm_detector import detect_sarcasm  # noqa: E402

            sarc = detect_sarcasm(review_text, result["label"], star_val)
            if sarc["is_sarcastic"]:
                st.warning(
                    f"⚠️ **Possible Sarcasm Detected**\n\n"
                    f"**Reason:** {sarc['reason']}\n\n"
                    f"**Severity:** {sarc['severity'].title()}  "
                    f"**Confidence:** {sarc['confidence'] * 100:.0f}%"
                )
            else:
                st.success("✅ No sarcasm indicators detected.")
        except Exception as exc:
            st.info(f"Sarcasm detection unavailable: {exc}")

    with add_col2:
        st.markdown("### 📐 TextBlob Polarity Gauge")
        try:
            import plotly.graph_objects as go  # noqa: E402

            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=polarity,
                    title={"text": "Polarity"},
                    gauge={
                        "axis": {"range": [-1, 1]},
                        "bar": {"color": "#00e5ff"},
                        "steps": [
                            {"range": [-1, -0.1], "color": "rgba(255,75,75,0.3)"},
                            {"range": [-0.1, 0.1], "color": "rgba(255,165,0,0.3)"},
                            {"range": [0.1, 1], "color": "rgba(0,200,81,0.3)"},
                        ],
                        "threshold": {
                            "line": {"color": "#b048ff", "width": 4},
                            "thickness": 0.75,
                            "value": polarity,
                        },
                    },
                )
            )
            fig_gauge.update_layout(
                template="plotly_dark",
                height=280,
                margin=dict(t=60, b=20, l=20, r=20),
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
        except Exception as exc:
            st.info(f"Gauge chart unavailable: {exc}")

    st.markdown("---")

    # ── PDF Download ─────────────────────────────────────────────────────────
    st.markdown("## 📄 Export Report")
    try:
        from src.pdf_exporter import export_report  # noqa: E402
        import io, tempfile, os  # noqa: E402

        pdf_data = {
            "review_text": review_text,
            "result": result,
            "word_weights": word_weights if "word_weights" in dir() else [],
        }
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            export_report(pdf_data, tmp_path)
            with open(tmp_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                "📥 Download PDF Report",
                data=pdf_bytes,
                file_name="reviewsense_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except (ImportError, AttributeError):
        st.info("📄 PDF export is not yet implemented. Run analysis to view results above.")