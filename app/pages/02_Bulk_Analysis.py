"""Bulk Review Analysis — ReviewSense Analytics."""

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
    page_title="Bulk Analysis — ReviewSense",
    page_icon="📂",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── UI imports ───────────────────────────────────────────────
from ui.sidebar import load_css, render_sidebar            # noqa: E402
from ui.components import (                                 # noqa: E402
    page_header, section_title, glass_card, step_card,
    metric_card,
)
from ui.theme import (                                      # noqa: E402
    apply_theme, POSITIVE_COLOR, NEGATIVE_COLOR,
    NEUTRAL_COLOR, ACCENT_BLUE, ACCENT_PURPLE,
)
from src.config import MODEL_NAMES, DOMAINS                 # noqa: E402
from utils import load_model                            # noqa: E402

load_css()
render_sidebar()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

page_header(
    "📂",
    "Bulk Review Analysis",
    "Upload datasets, run batch NLP pipelines, and generate comprehensive sentiment reports at scale",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HOW IT WORKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

section_title("How It Works", icon="📋")

s1, s2, s3, s4 = st.columns(4)
with s1:
    step_card(1, "Upload a CSV or Excel file containing your customer reviews dataset (max 50MB).")
with s2:
    step_card(2, "Map the correct column containing review text and optionally assign a domain tag.")
with s3:
    step_card(3, "Select analysis modules — Sentiment, Aspect-Based detection, and Sarcasm flagging.")
with s4:
    step_card(4, "Download the enriched dataset as CSV or a formatted PDF summary report.")

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPLOAD DATASET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

section_title("Upload Dataset", icon="📤")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], key="bulk_upload")

if uploaded_file is None:
    st.stop()

# ── Read CSV ─────────────────────────────────────────────────
import pandas as pd  # noqa: E402

try:
    df = pd.read_csv(uploaded_file)
except Exception as exc:
    st.error(f"Could not read CSV: {exc}")
    st.stop()

st.success(f"✅ File uploaded — {len(df):,} rows × {len(df.columns)} columns")
st.dataframe(df.head(5), use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COLUMN MAPPING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

section_title("Column Mapping", icon="🗂️")

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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANALYSIS SETTINGS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

section_title("Analysis Settings", icon="⚙️")

as1, as2, as3, as4 = st.columns(4)
with as1:
    run_sentiment = st.checkbox("Sentiment Analysis", value=True, key="bulk_sentiment")
with as2:
    run_aspect = st.checkbox("Aspect Detection", value=False, key="bulk_aspect")
with as3:
    run_sarcasm = st.checkbox("Sarcasm Detection", value=False, key="bulk_sarcasm")
with as4:
    model_name = st.selectbox("Model", ["best"] + MODEL_NAMES, index=0, key="bulk_model")

st.markdown("<br>", unsafe_allow_html=True)

# ── Analyze Button ───────────────────────────────────────────
st.markdown("<div class='gradient-btn'>", unsafe_allow_html=True)
if not st.button("🚀  Analyze All Reviews", use_container_width=True, key="bulk_analyze"):
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()
st.markdown("</div>", unsafe_allow_html=True)

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

# ── Build results dataframe ──────────────────────────────────
results_df = df.copy()
results_df["Sentiment"]   = [r["label_name"] for r in results]
results_df["Confidence"]  = [round(r["confidence"] * 100, 1) for r in results]
results_df["Polarity"]    = [round(r["polarity"], 4) for r in results]
results_df["Subjectivity"] = [round(r["subjectivity"], 4) for r in results]

st.markdown("---")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESULTS DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import plotly.graph_objects as go  # noqa: E402

total = len(results_df)
pos = (results_df["Sentiment"] == "Positive").sum()
neg = (results_df["Sentiment"] == "Negative").sum()
neu = (results_df["Sentiment"] == "Neutral").sum()

section_title("Results Dashboard", icon="📊")

sm1, sm2, sm3, sm4 = st.columns(4)
with sm1:
    metric_card("Total Reviews", f"{total:,}", color=ACCENT_BLUE)
with sm2:
    metric_card("Positive", f"{pos:,}  ({pos/total*100:.1f}%)", color=POSITIVE_COLOR)
with sm3:
    metric_card("Negative", f"{neg:,}  ({neg/total*100:.1f}%)", color=NEGATIVE_COLOR)
with sm4:
    metric_card("Neutral", f"{neu:,}  ({neu/total*100:.1f}%)", color=NEUTRAL_COLOR)

st.markdown("<br>", unsafe_allow_html=True)

# ── Sentiment Distribution (donut) ───────────────────────────
fig_pie = go.Figure(go.Pie(
    labels=["Positive", "Negative", "Neutral"],
    values=[pos, neg, neu],
    marker=dict(colors=[POSITIVE_COLOR, NEGATIVE_COLOR, NEUTRAL_COLOR]),
    hole=0.45,
    textinfo="label+percent",
))
apply_theme(fig_pie, title="Sentiment Distribution", height=380)
st.plotly_chart(fig_pie, use_container_width=True)

# ── Top Keywords ──────────────────────────────────────────────
section_title("Top Keywords", icon="🔑")

try:
    from collections import Counter  # noqa: E402

    def _top_words(series, n=15):
        words = " ".join(series.fillna("")).lower().split()
        stops = {"the","a","an","is","was","and","to","of","in","it","for","on","this","that","with","i","my","me","but"}
        return Counter(w for w in words if w not in stops and len(w) > 2).most_common(n)

    kw1, kw2 = st.columns(2)
    with kw1:
        pos_words = _top_words(results_df.loc[results_df["Sentiment"] == "Positive", text_column])
        if pos_words:
            fig_kw = go.Figure(go.Bar(
                x=[c for _, c in pos_words], y=[w for w, _ in pos_words],
                orientation="h", marker_color=POSITIVE_COLOR,
            ))
            apply_theme(fig_kw, title="Positive Keywords", height=400, margin=dict(l=120))
            fig_kw.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_kw, use_container_width=True)

    with kw2:
        neg_words = _top_words(results_df.loc[results_df["Sentiment"] == "Negative", text_column])
        if neg_words:
            fig_kw2 = go.Figure(go.Bar(
                x=[c for _, c in neg_words], y=[w for w, _ in neg_words],
                orientation="h", marker_color=NEGATIVE_COLOR,
            ))
            apply_theme(fig_kw2, title="Negative Keywords", height=400, margin=dict(l=120))
            fig_kw2.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_kw2, use_container_width=True)

except Exception:
    pass

# ── Full Results Table ────────────────────────────────────────
section_title("Full Results", icon="📋")

_disp = results_df[[text_column, "Sentiment", "Confidence", "Polarity"]].copy()
_disp[text_column] = _disp[text_column].str.slice(0, 80) + "…"
st.dataframe(_disp, use_container_width=True)

# ── AI Summary (Negative Reviews) ────────────────────────────
st.markdown("---")
section_title("AI Summary (Negative Reviews)", icon="🤖")

_neg_texts = results_df.loc[results_df["Sentiment"] == "Negative", text_column].fillna("").tolist()
if not _neg_texts:
    st.info("No negative reviews found — great product! 🎉")
else:
    try:
        from sumy.parsers.plaintext import PlaintextParser  # noqa: E402
        from sumy.nlp.tokenizers import Tokenizer           # noqa: E402
        from sumy.summarizers.lsa import LsaSummarizer      # noqa: E402

        _corpus = " ".join(_neg_texts[:500])
        _parser = PlaintextParser.from_string(_corpus, Tokenizer("english"))
        _summarizer = LsaSummarizer()
        _sents = _summarizer(_parser.document, sentences_count=5)
        _summary = " ".join(str(s) for s in _sents)
        if _summary.strip():
            glass_card(f"<p style='color:#e2e8f0;line-height:1.8;'>{_summary}</p>", icon="🤖")
        else:
            st.info("Could not generate summary for the available text.")
    except ImportError:
        st.info("Install `sumy` for AI-powered summaries.")
    except Exception as exc:
        st.info(f"Summary generation error: {exc}")

# ── Product Recommendation Score ──────────────────────────────
st.markdown("---")
section_title("Product Recommendation Score", icon="🏆")

_rec_score = round((pos / total) * 100, 1) if total > 0 else 0.0
fig_rec = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=_rec_score,
    title={"text": "Recommendation Score"},
    delta={"reference": 70},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": ACCENT_BLUE},
        "steps": [
            {"range": [0, 40],   "color": "rgba(239,68,68,0.15)"},
            {"range": [40, 70],  "color": "rgba(245,158,11,0.15)"},
            {"range": [70, 100], "color": "rgba(34,197,94,0.15)"},
        ],
        "threshold": {"line": {"color": ACCENT_PURPLE, "width": 4}, "thickness": 0.75, "value": _rec_score},
    },
))
apply_theme(fig_rec, height=320, margin=dict(t=60, b=20, l=20, r=20))
st.plotly_chart(fig_rec, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXPORT RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("---")
section_title("Export Results", icon="📥")

_export_df = results_df.drop(columns=["_text_display"], errors="ignore")

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