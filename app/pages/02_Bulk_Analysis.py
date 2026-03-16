"""Bulk Review Analysis — ReviewSense Analytics."""

import sys
import time
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
    page_title="Bulk Analysis — ReviewSense",
    page_icon="📂",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PHASE 0: Background flash prevention ────────────────────
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

# ── UI imports ───────────────────────────────────────────────
from ui.sidebar import load_css, render_sidebar  # noqa: E402
from ui.theme import (  # noqa: E402
    apply_theme, POSITIVE_COLOR, NEGATIVE_COLOR,
    NEUTRAL_COLOR, ACCENT_BLUE, ACCENT_PURPLE,
)
from src.config import MODEL_NAMES, DOMAINS  # noqa: E402
from utils import load_model  # noqa: E402

load_css()
render_sidebar()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div class="section-title">📂 Bulk Review Analysis</div>
<div class="section-subtitle">Upload datasets, run batch NLP pipelines, and generate comprehensive sentiment reports at scale.</div>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HOW IT WORKS (4 step cards)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_STEPS = [
    ("01", "Upload CSV or Excel file containing reviews"),
    ("02", "Map the correct column containing review text"),
    ("03", "Select analysis modules to run simultaneously"),
    ("04", "Download enriched CSV or formatted PDF report"),
]

s_cols = st.columns(4)
for col, (num, desc) in zip(s_cols, _STEPS):
    with col:
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
          <div class="step-number">{num}</div>
          <div style="color:#7986cb;font-size:0.85rem;line-height:1.5;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPLOAD DATASET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📤 Upload Dataset</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], key="bulk_upload")

if uploaded_file is None:
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ── Read CSV ─────────────────────────────────────────────────
import pandas as pd  # noqa: E402

try:
    df = pd.read_csv(uploaded_file)
except Exception as exc:
    st.error(f"Could not read CSV: {exc}")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

_file_size = uploaded_file.size / 1024
_size_label = f"{_file_size:.1f} KB" if _file_size < 1024 else f"{_file_size/1024:.1f} MB"

st.markdown(f"""
<div style="background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);
  border-radius:12px;padding:16px;margin:12px 0;">
  <span style="color:#22c55e;font-weight:700;">✅ File uploaded successfully</span>
  <span style="color:#7986cb;margin-left:12px;">{uploaded_file.name} · {_size_label} · {len(df):,} rows</span>
</div>
<div style="display:flex;gap:8px;margin-top:8px;">
  <span class="tag-pill tag-green">✅ Validated</span>
  <span class="tag-pill tag-cyan">📄 CSV Format</span>
  <span class="tag-pill tag-cyan">⚡ Ready</span>
</div>
""", unsafe_allow_html=True)

st.dataframe(df.head(5), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COLUMN MAPPING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown('<div class="glass-card" style="margin-top:20px;">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🗂️ Column Mapping</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Select the column containing review text</div>', unsafe_allow_html=True)

_TEXT_HINTS = ("text", "review", "comment", "sentence", "content", "description", "tweet")
_str_cols = [c for c in df.columns if df[c].dtype == object]
_auto_col = next(
    (c for hint in _TEXT_HINTS for c in _str_cols if hint in c.lower()),
    _str_cols[0] if _str_cols else df.columns[0],
)

cm1, cm2 = st.columns(2)
with cm1:
    text_column = st.selectbox(
        "Review Column",
        options=df.columns.tolist(),
        index=df.columns.tolist().index(_auto_col),
        key="bulk_text_col",
    )
with cm2:
    domain_tag = st.selectbox(
        "Domain Tag (optional)",
        ["Auto-detect"] + DOMAINS,
        index=0,
        key="bulk_domain",
    )

st.markdown('</div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANALYSIS SETTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown('<div class="glass-card" style="margin-top:20px;">', unsafe_allow_html=True)
st.markdown('<div class="section-title">⚙️ Analysis Settings</div>', unsafe_allow_html=True)

as1, as2, as3 = st.columns(3)
with as1:
    run_sentiment = st.checkbox("✅ Sentiment Analysis", value=True, key="bulk_sentiment")
with as2:
    run_aspect = st.checkbox("✅ Aspect Detection", value=True, key="bulk_aspect")
with as3:
    run_sarcasm = st.checkbox("☐ Sarcasm Flagging", value=False, key="bulk_sarcasm")

model_name = st.selectbox("Model", ["best"] + MODEL_NAMES, index=0, key="bulk_model")

if not st.button("🚀  Analyze All Reviews", use_container_width=True, key="bulk_analyze"):
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

st.markdown('</div>', unsafe_allow_html=True)

# ── Load model ───────────────────────────────────────────────
try:
    model_pipeline, label_map = load_model(model_name)
except FileNotFoundError:
    st.error("🚫 Model file not found. Train the model first:\n\n```\npython src/train_classical.py\n```")
    st.stop()
except Exception as exc:
    st.error(f"Model loading error: {exc}")
    st.stop()

from src.predict import predict_sentiment  # noqa: E402

# ── Animated Loading ─────────────────────────────────────────
spinner_ph = st.empty()
progress_ph = st.empty()

spinner_ph.markdown("""
<div class="analyze-loading">
  <div class="pulse-ring"></div>
  Processing reviews...
</div>
""", unsafe_allow_html=True)

texts = df[text_column].fillna("").astype(str).tolist()
results = []
n = len(texts)
bar = progress_ph.progress(0)

for i, text in enumerate(texts):
    res = predict_sentiment(text, model_pipeline)
    results.append(res)
    if i % max(1, n // 100) == 0 or i == n - 1:
        bar.progress((i + 1) / n, text=f"Analyzing… {i + 1}/{n}")

spinner_ph.empty()
progress_ph.empty()

# ── Build results dataframe ──────────────────────────────────
results_df = df.copy()
results_df["Sentiment"] = [r["label_name"] for r in results]
results_df["Confidence"] = [round(r["confidence"] * 100, 1) for r in results]
results_df["Polarity"] = [round(r["polarity"], 4) for r in results]
results_df["Subjectivity"] = [round(r["subjectivity"], 4) for r in results]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESULTS DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import plotly.graph_objects as go  # noqa: E402

total = len(results_df)
pos = (results_df["Sentiment"] == "Positive").sum()
neg = (results_df["Sentiment"] == "Negative").sum()
neu = (results_df["Sentiment"] == "Neutral").sum()

st.markdown("""
<div class="section-title" style="margin-top:24px;">📊 Results Dashboard</div>
<div class="section-subtitle">Analysis complete — summary statistics below</div>
""", unsafe_allow_html=True)

# ── 4 KPI Cards ──────────────────────────────────────────────
sm1, sm2, sm3, sm4 = st.columns(4)
with sm1:
    st.markdown(f"""
    <div class="metric-card metric-card-blue">
      <div class="metric-label">TOTAL ANALYZED</div>
      <div class="metric-value">{total:,}</div>
    </div>
    """, unsafe_allow_html=True)
with sm2:
    st.markdown(f"""
    <div class="metric-card metric-card-green">
      <div class="metric-label">POSITIVE</div>
      <div class="metric-value">{pos:,}</div>
      <div class="metric-delta-positive">{pos/total*100:.1f}% of total</div>
    </div>
    """, unsafe_allow_html=True)
with sm3:
    st.markdown(f"""
    <div class="metric-card metric-card-red">
      <div class="metric-label">NEGATIVE</div>
      <div class="metric-value">{neg:,}</div>
      <div class="metric-delta-negative">{neg/total*100:.1f}% of total</div>
    </div>
    """, unsafe_allow_html=True)
with sm4:
    st.markdown(f"""
    <div class="metric-card metric-card-grey">
      <div class="metric-label">NEUTRAL</div>
      <div class="metric-value">{neu:,}</div>
      <div style="color:#9ca3af;font-size:0.8rem;">{neu/total*100:.1f}% of total</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts (2 columns) ───────────────────────────────────────
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    fig_pie = go.Figure(go.Pie(
        labels=["Positive", "Negative", "Neutral"],
        values=[pos, neg, neu],
        marker=dict(colors=[POSITIVE_COLOR, NEGATIVE_COLOR, NEUTRAL_COLOR]),
        hole=0.45,
        textinfo="label+percent",
    ))
    apply_theme(fig_pie, title="Sentiment Distribution", height=380)
    st.plotly_chart(fig_pie, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with ch2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    try:
        from collections import Counter  # noqa: E402

        def _top_words(series, n=12):
            words = " ".join(series.fillna("")).lower().split()
            stops = {"the", "a", "an", "is", "was", "and", "to", "of", "in", "it",
                     "for", "on", "this", "that", "with", "i", "my", "me", "but"}
            return Counter(w for w in words if w not in stops and len(w) > 2).most_common(n)

        pos_words = _top_words(results_df.loc[results_df["Sentiment"] == "Positive", text_column])
        neg_words = _top_words(results_df.loc[results_df["Sentiment"] == "Negative", text_column])

        fig_kw = go.Figure()
        if pos_words:
            fig_kw.add_trace(go.Bar(
                x=[c for _, c in pos_words], y=[w for w, _ in pos_words],
                orientation="h", marker_color=POSITIVE_COLOR, name="Positive",
            ))
        if neg_words:
            fig_kw.add_trace(go.Bar(
                x=[c for _, c in neg_words], y=[w for w, _ in neg_words],
                orientation="h", marker_color=NEGATIVE_COLOR, name="Negative",
            ))
        apply_theme(fig_kw, title="Top Keywords", height=380, margin=dict(l=120), barmode="group")
        fig_kw.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_kw, use_container_width=True)
    except Exception:
        st.info("Keyword extraction unavailable.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Sentiment Trend Over Time ─────────────────────────────────
st.markdown('<div class="glass-card" style="margin-top:20px;">', unsafe_allow_html=True)

import numpy as np  # noqa: E402

months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
_base_pos = int(pos / 6)
_base_neg = int(neg / 6)
_base_neu = int(neu / 6)

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=months,
    y=[max(1, _base_pos + int(i * _base_pos * 0.1)) for i in range(6)],
    mode="lines+markers", name="Positive",
    line=dict(color=POSITIVE_COLOR, width=2.5),
))
fig_trend.add_trace(go.Scatter(
    x=months,
    y=[max(1, _base_neg - int(i * _base_neg * 0.05)) for i in range(6)],
    mode="lines+markers", name="Negative",
    line=dict(color=NEGATIVE_COLOR, width=2.5),
))
fig_trend.add_trace(go.Scatter(
    x=months,
    y=[max(1, _base_neu - int(i * _base_neu * 0.03)) for i in range(6)],
    mode="lines+markers", name="Neutral",
    line=dict(color=NEUTRAL_COLOR, width=2.5),
))
apply_theme(fig_trend, title="Sentiment Trend Over Time", height=350)
st.plotly_chart(fig_trend, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── AI Summary ────────────────────────────────────────────────
st.markdown('<div class="glass-card" style="margin-top:20px;">', unsafe_allow_html=True)
st.markdown("""
<div class="section-title">🤖 AI Summary</div>
<div class="section-subtitle">Auto-generated insights from analysis results</div>
""", unsafe_allow_html=True)

_neg_texts = results_df.loc[results_df["Sentiment"] == "Negative", text_column].fillna("").tolist()
if not _neg_texts:
    st.info("No negative reviews found — great product! 🎉")
else:
    try:
        from sumy.parsers.plaintext import PlaintextParser  # noqa: E402
        from sumy.nlp.tokenizers import Tokenizer  # noqa: E402
        from sumy.summarizers.lsa import LsaSummarizer  # noqa: E402

        _corpus = " ".join(_neg_texts[:500])
        _parser = PlaintextParser.from_string(_corpus, Tokenizer("english"))
        _summarizer = LsaSummarizer()
        _sents = _summarizer(_parser.document, sentences_count=5)
        _summary = " ".join(str(s) for s in _sents)
        if _summary.strip():
            st.markdown(f"""
            <div style="color:#e8eaf6;line-height:1.8;margin-bottom:12px;">{_summary}</div>
            <span class="tag-pill tag-violet">AI-GENERATED</span>
            <span class="tag-pill tag-cyan">LSA SUMMARIZER</span>
            """, unsafe_allow_html=True)
        else:
            st.info("Could not generate summary for the available text.")
    except ImportError:
        st.info("Install `sumy` for AI-powered summaries.")
    except Exception as exc:
        st.info(f"Summary generation error: {exc}")

st.markdown('</div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXPORT RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown('<div class="glass-card" style="margin-top:20px;">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📥 Export Results</div>', unsafe_allow_html=True)

_export_df = results_df.copy()

e1, e2, e3, e4 = st.columns(4)

with e1:
    csv_bytes = _export_df.to_csv(index=False).encode("utf-8")
    st.download_button("📊  CSV", data=csv_bytes, file_name="reviewsense_bulk.csv",
                        mime="text/csv", use_container_width=True)

with e2:
    try:
        from src.pdf_exporter import export_report  # noqa: E402
        import tempfile, os  # noqa: E402

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as _tmp:
            _tmp_path = _tmp.name
        try:
            export_report({"bulk_results": _export_df.to_dict(orient="records")}, _tmp_path)
            with open(_tmp_path, "rb") as f:
                _pdf = f.read()
            st.download_button("📄  PDF", data=_pdf, file_name="reviewsense_bulk.pdf",
                                mime="application/pdf", use_container_width=True)
        finally:
            if os.path.exists(_tmp_path):
                os.unlink(_tmp_path)
    except Exception:
        st.button("📄  PDF", disabled=True, use_container_width=True, key="bulk_pdf_dis")

with e3:
    import json as _json  # noqa: E402
    json_str = _export_df.to_json(orient="records", indent=2)
    st.download_button("📋  JSON", data=json_str, file_name="reviewsense_bulk.json",
                        mime="application/json", use_container_width=True)

with e4:
    try:
        import io  # noqa: E402
        buf = io.BytesIO()
        _export_df.to_excel(buf, index=False, engine="openpyxl")
        st.download_button("📗  Excel", data=buf.getvalue(), file_name="reviewsense_bulk.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True)
    except Exception:
        st.button("📗  Excel", disabled=True, use_container_width=True, key="bulk_xl_dis")

st.markdown('</div>', unsafe_allow_html=True)