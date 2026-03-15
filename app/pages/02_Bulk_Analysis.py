"""Bulk Review Analysis page for ReviewSense Analytics."""

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
    page_title="Bulk Analysis — ReviewSense",
    layout="wide",
    page_icon="📂",
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
from app.utils import render_sidebar  # noqa: E402

sidebar_opts = render_sidebar()

# ---------------------------------------------------------------------------
# Model loading (cached)
# ---------------------------------------------------------------------------
@st.cache_resource
def load_model(model_name: str = "best"):
    from src.predict import load_model as _load
    return _load(model_name)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("<h1>📂 Bulk Review Analysis</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#9e9eb8;'>Upload a CSV file containing reviews for automated "
    "batch sentiment analysis, visualizations, and AI-generated summary.</p>",
    unsafe_allow_html=True,
)
st.markdown(
    """<div class='rs-card'>
    <b>Instructions:</b>
    <ul style='margin-top:0.5rem;color:#9e9eb8;'>
    <li>Upload a <code>.csv</code> file with at least one text column.</li>
    <li>The app will auto-detect the review column — confirm or change it.</li>
    <li>Click <b>Analyze All Reviews</b> to run batch sentiment analysis.</li>
    <li>Download results as CSV or a full PDF report.</li>
    </ul></div>""",
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------------
uploaded_file = st.file_uploader("📤 Upload CSV file", type=["csv"], key="bulk_upload")

if uploaded_file is None:
    st.stop()

# ---------------------------------------------------------------------------
# Preview & column selection
# ---------------------------------------------------------------------------
import pandas as pd  # noqa: E402

try:
    df = pd.read_csv(uploaded_file)
except Exception as exc:
    st.error(f"Could not read CSV: {exc}")
    st.stop()

st.markdown(f"**Preview** ({len(df):,} rows × {len(df.columns)} columns)")
st.dataframe(df.head(5), use_container_width=True)

# Auto-detect text column
_TEXT_HINTS = ("text", "review", "comment", "sentence", "content", "description", "tweet")
_str_cols = [c for c in df.columns if df[c].dtype == object]
_auto_col = next(
    (c for hint in _TEXT_HINTS for c in _str_cols if hint in c.lower()),
    _str_cols[0] if _str_cols else df.columns[0],
)

text_column = st.selectbox(
    "🔤 Select the review / text column:",
    options=df.columns.tolist(),
    index=df.columns.tolist().index(_auto_col),
    key="bulk_text_col",
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Analyze button
# ---------------------------------------------------------------------------
if not st.button("🚀 Analyze All Reviews", use_container_width=True, key="bulk_analyze_btn"):
    st.stop()

# ── Load model ───────────────────────────────────────────────────────────
try:
    model_pipeline, label_map = load_model(sidebar_opts["model"])
except FileNotFoundError:
    st.error(
        "🚫 Model file not found. Train the model first:\n\n"
        "```\npython src/train_classical.py\n```"
    )
    st.stop()
except Exception as exc:
    st.error(f"Model loading error: {exc}")
    st.stop()

from src.predict import predict_sentiment  # noqa: E402

texts = df[text_column].fillna("").astype(str).tolist()
results = []

progress_bar = st.progress(0, text="Analyzing reviews…")
n = len(texts)

for i, text in enumerate(texts):
    res = predict_sentiment(text, model_pipeline)
    results.append(res)
    if i % max(1, n // 100) == 0 or i == n - 1:
        progress_bar.progress((i + 1) / n, text=f"Analyzing… {i + 1}/{n}")

progress_bar.empty()

# Build results dataframe
results_df = df.copy()
results_df["Sentiment"] = [r["label_name"] for r in results]
results_df["Confidence"] = [round(r["confidence"] * 100, 1) for r in results]
results_df["Polarity"] = [round(r["polarity"], 4) for r in results]
results_df["Subjectivity"] = [round(r["subjectivity"], 4) for r in results]
results_df["_text_display"] = results_df[text_column].str.slice(0, 80) + "…"

st.markdown("---")

# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------
import plotly.graph_objects as go  # noqa: E402

total = len(results_df)
pos = (results_df["Sentiment"] == "Positive").sum()
neg = (results_df["Sentiment"] == "Negative").sum()
neu = (results_df["Sentiment"] == "Neutral").sum()

st.markdown("## 📊 Summary")
sm1, sm2, sm3, sm4 = st.columns(4)
sm1.metric("📝 Total Reviews", f"{total:,}")
sm2.metric("✅ Positive", f"{pos:,} ({pos/total*100:.1f}%)")
sm3.metric("❌ Negative", f"{neg:,} ({neg/total*100:.1f}%)")
sm4.metric("🟡 Neutral", f"{neu:,} ({neu/total*100:.1f}%)")

# ── Pie chart ──────────────────────────────────────────────────────────────
fig_pie = go.Figure(
    go.Pie(
        labels=["Positive", "Negative", "Neutral"],
        values=[pos, neg, neu],
        marker=dict(colors=["#00c851", "#ff4b4b", "#ffa500"]),
        hole=0.4,
    )
)
fig_pie.update_layout(template="plotly_dark", title="Sentiment Distribution", height=350)
st.plotly_chart(fig_pie, use_container_width=True)

# ── Full results table ─────────────────────────────────────────────────────
st.markdown("## 📋 Full Results")
display_cols = ["_text_display", "Sentiment", "Confidence", "Polarity"]
display_df = results_df[display_cols].rename(columns={"_text_display": "Review (truncated)"})
st.dataframe(display_df, use_container_width=True)

# ── Word clouds ────────────────────────────────────────────────────────────
st.markdown("## ☁️ Word Clouds")
wc_col1, wc_col2 = st.columns(2)

_pos_texts = " ".join(results_df.loc[results_df["Sentiment"] == "Positive", text_column].fillna(""))
_neg_texts = " ".join(results_df.loc[results_df["Sentiment"] == "Negative", text_column].fillna(""))

try:
    from wordcloud import WordCloud  # noqa: E402
    import matplotlib.pyplot as plt  # noqa: E402

    with wc_col1:
        st.markdown("**✅ Positive Reviews**")
        if _pos_texts.strip():
            wc_pos = WordCloud(
                width=600, height=300, background_color="#0a0a0f",
                colormap="Greens", max_words=80,
            ).generate(_pos_texts)
            fig_wc, ax = plt.subplots(figsize=(6, 3))
            fig_wc.patch.set_facecolor("#0a0a0f")
            ax.imshow(wc_pos, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig_wc)
        else:
            st.info("No positive reviews to display.")

    with wc_col2:
        st.markdown("**❌ Negative Reviews**")
        if _neg_texts.strip():
            wc_neg = WordCloud(
                width=600, height=300, background_color="#0a0a0f",
                colormap="Reds", max_words=80,
            ).generate(_neg_texts)
            fig_wc2, ax2 = plt.subplots(figsize=(6, 3))
            fig_wc2.patch.set_facecolor("#0a0a0f")
            ax2.imshow(wc_neg, interpolation="bilinear")
            ax2.axis("off")
            st.pyplot(fig_wc2)
        else:
            st.info("No negative reviews to display.")
except ImportError:
    st.info("Install `wordcloud` and `matplotlib` for word cloud visualizations.")

# ── AI Summary ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 🤖 AI Summary (Negative Reviews)")

_neg_review_texts = results_df.loc[results_df["Sentiment"] == "Negative", text_column].fillna("").tolist()
if not _neg_review_texts:
    st.info("No negative reviews found — great product! 🎉")
else:
    try:
        from sumy.parsers.plaintext import PlaintextParser  # noqa: E402
        from sumy.nlp.tokenizers import Tokenizer  # noqa: E402
        from sumy.summarizers.lsa import LsaSummarizer  # noqa: E402

        _corpus = " ".join(_neg_review_texts[:500])
        _parser = PlaintextParser.from_string(_corpus, Tokenizer("english"))
        _summarizer = LsaSummarizer()
        _summary_sentences = _summarizer(_parser.document, sentences_count=5)
        _summary_text = " ".join(str(s) for s in _summary_sentences)
        if _summary_text.strip():
            st.markdown(
                f"<div class='rs-card'><p style='color:#e8eaf6;line-height:1.8;'>"
                f"{_summary_text}</p></div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("Could not generate summary for the available text.")
    except ImportError:
        st.info("Install `sumy` for AI-powered summaries.")
    except Exception as exc:
        st.info(f"Summary generation error: {exc}")

# ── Recommendation score ───────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 🏆 Product Recommendation Score")
_rec_score = round((pos / total) * 100, 1) if total > 0 else 0.0

fig_rec = go.Figure(
    go.Indicator(
        mode="gauge+number+delta",
        value=_rec_score,
        title={"text": "Recommendation Score"},
        delta={"reference": 70},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#00e5ff"},
            "steps": [
                {"range": [0, 40], "color": "rgba(255,75,75,0.3)"},
                {"range": [40, 70], "color": "rgba(255,165,0,0.3)"},
                {"range": [70, 100], "color": "rgba(0,200,81,0.3)"},
            ],
            "threshold": {
                "line": {"color": "#b048ff", "width": 4},
                "thickness": 0.75,
                "value": _rec_score,
            },
        },
    )
)
fig_rec.update_layout(
    template="plotly_dark",
    height=320,
    margin=dict(t=60, b=20, l=20, r=20),
)
st.plotly_chart(fig_rec, use_container_width=True)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("## 📥 Export Results")

exp_col1, exp_col2 = st.columns(2)

_export_df = results_df.drop(columns=["_text_display"], errors="ignore")

with exp_col1:
    csv_bytes = _export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📊 Download Results CSV",
        data=csv_bytes,
        file_name="reviewsense_bulk_results.csv",
        mime="text/csv",
        use_container_width=True,
    )

with exp_col2:
    try:
        from src.pdf_exporter import export_report  # noqa: E402
        import os, tempfile  # noqa: E402

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as _tmp:
            _tmp_path = _tmp.name
        try:
            export_report({"bulk_results": _export_df.to_dict(orient="records")}, _tmp_path)
            with open(_tmp_path, "rb") as f:
                _pdf_bytes = f.read()
            st.download_button(
                "📄 Download Full PDF Report",
                data=_pdf_bytes,
                file_name="reviewsense_bulk_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        finally:
            if os.path.exists(_tmp_path):
                os.unlink(_tmp_path)
    except (ImportError, AttributeError):
        st.button("📄 Download Full PDF Report", disabled=True, use_container_width=True)
        st.caption("PDF export not yet implemented.")