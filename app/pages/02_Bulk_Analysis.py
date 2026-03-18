"""Bulk Review Analysis — ReviewSense Analytics."""

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

st.set_page_config(page_title="Bulk Analysis — ReviewSense", page_icon="📂", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"],
[data-testid="stMain"],.main,.block-container{background-color:#070b14!important;background:#070b14!important}
[data-testid="stSidebarNav"],[data-testid="stSidebarNav"] *{display:none!important}
</style>""", unsafe_allow_html=True)

from ui.sidebar import load_css, render_sidebar  # noqa: E402
from ui.theme import apply_theme, POSITIVE_COLOR, NEGATIVE_COLOR, NEUTRAL_COLOR  # noqa: E402
from src.config import MODEL_NAMES, DOMAINS  # noqa: E402
from src.analytics import compute_metrics, generate_summary, extract_keywords, build_sentiment_pie, build_keywords_chart, build_trend_chart  # noqa: E402
from src.exporter import render_export_buttons  # noqa: E402
from utils import load_model  # noqa: E402

load_css()
render_sidebar()

# ━━━ SESSION STATE DEFAULTS ━━━
for _key, _default in [
    ("bulk_results_data", None),
    ("bulk_results_df", None),
    ("bulk_text_col_used", None),
    ("bulk_sarcasm_was_on", False),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ━━━ HEADER ━━━
st.markdown("""<div class="glass-card">
  <div class="section-title">📂 Bulk Review Analysis</div>
  <div class="section-subtitle" style="margin-bottom:0;">Upload datasets, run batch NLP pipelines, and generate comprehensive sentiment reports at scale.</div>
</div>""", unsafe_allow_html=True)

# ━━━ HOW IT WORKS ━━━
st.markdown('<div class="section-title">📋 How It Works</div><div class="section-subtitle" style="margin-bottom:12px;">Follow these 4 steps</div>', unsafe_allow_html=True)
_S = [("01","Upload CSV or Excel file"),("02","Map the text column"),("03","Select analysis modules"),("04","Download enriched report")]
sc = st.columns(4)
for c,(n,d) in zip(sc,_S):
    with c:
        st.markdown(f'<div class="glass-card" style="text-align:center;"><div class="step-number">{n}</div><div style="color:#7986cb;font-size:0.85rem;line-height:1.5;">{d}</div></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━ UPLOAD (unified Pattern B) ━━━
with st.container():
    st.markdown("""<div class="glass-card-header">
      <div class="upload-zone-header">
        <div class="upload-icon-circle">📂</div>
        <div><div class="upload-text-primary">Drop your review dataset here</div>
        <div class="upload-text-secondary">Drag and drop or click Browse to upload</div></div>
      </div>
      <div class="upload-badges">
        <span class="upload-badge upload-badge-csv">CSV</span>
        <span class="upload-badge upload-badge-excel">XLSX</span>
        <span class="upload-badge upload-badge-limit">Max 200MB</span>
      </div>
    </div>""", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["csv","xlsx"], label_visibility="collapsed", key="bulk_upload")
    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

if uploaded_file is None:
    # Clear stale results when file is removed
    st.session_state.bulk_results_data = None
    st.session_state.bulk_results_df = None
    st.stop()

import pandas as pd  # noqa: E402
try:
    df = pd.read_csv(uploaded_file)
except Exception as exc:
    st.error(f"Could not read CSV: {exc}"); st.stop()

_fs = uploaded_file.size/1024
_sl = f"{_fs:.1f} KB" if _fs < 1024 else f"{_fs/1024:.1f} MB"

st.markdown(f"""<div class="glass-card">
  <span style="color:#22c55e;font-weight:700;">✅ File uploaded</span>
  <span style="color:#7986cb;margin-left:12px;">{uploaded_file.name} · {_sl} · {len(df):,} rows</span>
  <div style="display:flex;gap:8px;margin-top:8px;">
    <span class="tag-pill tag-green">✅ Validated</span><span class="tag-pill tag-cyan">📄 CSV</span><span class="tag-pill tag-cyan">⚡ Ready</span>
  </div>
</div>""", unsafe_allow_html=True)

st.dataframe(df.head(5), use_container_width=True)
st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━ COLUMN MAPPING (Pattern B) ━━━
_TH = ("text","review","comment","sentence","content","description","tweet")
_sc = [c for c in df.columns if df[c].dtype == object]
_ac = next((c for h in _TH for c in _sc if h in c.lower()), _sc[0] if _sc else df.columns[0])

with st.container():
    st.markdown('<div class="glass-card-header"><div class="section-title">🗂️ Column Mapping</div><div class="section-subtitle">Select the column containing review text</div></div>', unsafe_allow_html=True)
    cm1,cm2 = st.columns(2)
    with cm1:
        text_column = st.selectbox("Review Column", options=df.columns.tolist(), index=df.columns.tolist().index(_ac), key="bulk_text_col")
    with cm2:
        domain_tag = st.selectbox("Domain Tag", ["Auto-detect"]+DOMAINS, index=0, key="bulk_domain")
    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━ ANALYSIS SETTINGS (Pattern B) ━━━
with st.container():
    st.markdown('<div class="glass-card-header"><div class="section-title">⚙️ Analysis Settings</div><div class="section-subtitle">Choose modules and model</div></div>', unsafe_allow_html=True)
    cl,cr = st.columns([2,1])
    with cl:
        a1,a2,a3 = st.columns(3)
        with a1: run_sentiment = st.toggle("Sentiment", value=True, key="bulk_sentiment")
        with a2: run_aspect = st.toggle("Aspect", value=True, key="bulk_aspect")
        with a3: run_sarcasm = st.toggle("Sarcasm", value=False, key="bulk_sarcasm")
    with cr:
        model_name = st.selectbox("Model", ["best"]+MODEL_NAMES, index=0, key="bulk_model")
    # Dynamic badges reflecting actual toggle state
    _badges = []
    for _lbl, _on in [("Sentiment", run_sentiment), ("Aspect", run_aspect), ("Sarcasm", run_sarcasm)]:
        if _on:
            _badges.append(f'<span class="tag-pill tag-green">✅ {_lbl}</span>')
        else:
            _badges.append(f'<span class="tag-pill" style="background:rgba(156,163,175,0.15);color:#9ca3af;">◻ {_lbl}</span>')
    st.markdown(f'<div style="margin-top:4px;">{" ".join(_badges)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# Large dataset warning
if len(df) > 1500:
    st.warning(f"⚠️ Large dataset detected ({len(df):,} rows). Optimized batch mode enabled — processing may take a moment.")

# ━━━ ANALYZE BUTTON ━━━
analyze_clicked = st.button("🚀  Analyze All Reviews", use_container_width=True, key="bulk_analyze")

if analyze_clicked:
    from src.pipeline.inference import run_pipeline_batch, preload_models  # noqa: E402

    # Preload models eagerly (cached — instant on subsequent runs)
    preload_models()

    sph = st.empty(); pph = st.empty()
    sph.markdown('<div class="analyze-loading"><div class="spin-ring"></div> Processing reviews with RoBERTa...</div>', unsafe_allow_html=True)
    texts = df[text_column].fillna("").astype(str).tolist()

    bar = pph.progress(0)

    # Real-time progress callback from pipeline
    def _progress(pct, msg):
        bar.progress(min(pct, 100), text=msg)

    results = run_pipeline_batch(
        texts,
        enable_sarcasm=run_sarcasm,
        enable_aspects=run_aspect,
        progress_callback=_progress,
    )

    time.sleep(0.2)
    sph.empty(); pph.empty()

    # In-place column assignment (no df.copy() — saves memory)
    rdf = df.copy()
    rdf["Sentiment"] = [r["sentiment"] for r in results]
    rdf["Confidence"] = [round(r["confidence"]*100,1) for r in results]
    rdf["Polarity"] = [round(r["polarity"],4) for r in results]
    rdf["Subjectivity"] = [round(r["subjectivity"],4) for r in results]
    rdf["Language"] = [r.get("language_name", "Unknown") for r in results]
    rdf["Sarcasm"] = [("Yes" if r.get("sarcasm", {}).get("is_sarcastic") else "No") if r.get("sarcasm") else "N/A" for r in results]

    # Persist in session state — prevents flicker on rerender
    st.session_state.bulk_results_data = results
    st.session_state.bulk_results_df = rdf
    st.session_state.bulk_text_col_used = text_column
    st.session_state.bulk_sarcasm_was_on = run_sarcasm

# ━━━ RENDER RESULTS FROM SESSION STATE (anti-flicker) ━━━
rdf = st.session_state.bulk_results_df
if rdf is None:
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    st.stop()

text_column = st.session_state.bulk_text_col_used or text_column
results = st.session_state.bulk_results_data or []
sarcasm_was_on = st.session_state.bulk_sarcasm_was_on

# ── Centralized metrics ──
import plotly.graph_objects as go  # noqa: E402
metrics = compute_metrics(rdf)
total, pos, neg, neu, sarc_count = metrics["total"], metrics["pos"], metrics["neg"], metrics["neu"], metrics["sarc_count"]

st.markdown('<div class="glass-card"><div class="section-title">📊 Results Dashboard</div><div class="section-subtitle" style="margin-bottom:0;">Analysis complete</div></div>', unsafe_allow_html=True)

# ── Metric cards — 5 columns if sarcasm was on, 4 otherwise ──
if sarcasm_was_on:
    s1,s2,s3,s4,s5 = st.columns(5)
else:
    s1,s2,s3,s4 = st.columns(4)

with s1: st.markdown(f'<div class="metric-card metric-card-blue"><div class="metric-label">TOTAL</div><div class="metric-value">{total:,}</div><div style="color:var(--subtext);font-size:0.8rem;margin-top:4px;">{total:,} reviews</div></div>', unsafe_allow_html=True)
with s2: st.markdown(f'<div class="metric-card metric-card-green"><div class="metric-label">POSITIVE</div><div class="metric-value">{pos:,}</div><div class="metric-delta-positive">{pos/total*100:.1f}%</div></div>', unsafe_allow_html=True)
with s3: st.markdown(f'<div class="metric-card metric-card-red"><div class="metric-label">NEGATIVE</div><div class="metric-value">{neg:,}</div><div class="metric-delta-negative">{neg/total*100:.1f}%</div></div>', unsafe_allow_html=True)
with s4: st.markdown(f'<div class="metric-card metric-card-grey"><div class="metric-label">NEUTRAL</div><div class="metric-value">{neu:,}</div><div style="color:var(--neutral);font-size:0.8rem;margin-top:4px;">{neu/total*100:.1f}%</div></div>', unsafe_allow_html=True)
if sarcasm_was_on:
    with s5: st.markdown(f'<div class="metric-card metric-card-amber"><div class="metric-label">SARCASM</div><div class="metric-value">{sarc_count:,}</div><div style="color:var(--amber);font-size:0.8rem;margin-top:4px;">{sarc_count/total*100:.1f}% detected</div></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── Results dataframe ──
display_cols = [c for c in ["Sentiment","Confidence","Polarity","Language","Sarcasm"] if c in rdf.columns]
if text_column in rdf.columns:
    display_cols = [text_column] + display_cols
# Remove Sarcasm column if it wasn't enabled
if not sarcasm_was_on and "Sarcasm" in display_cols:
    display_cols.remove("Sarcasm")
st.dataframe(rdf[display_cols], use_container_width=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── Charts (using centralized builders) ──
c1,c2 = st.columns(2)
with c1:
    fp = build_sentiment_pie(pos, neg, neu, POSITIVE_COLOR, NEGATIVE_COLOR, NEUTRAL_COLOR)
    apply_theme(fp, title="Sentiment Distribution", height=380)
    st.plotly_chart(fp, use_container_width=True, key="bulk_pie")
with c2:
    try:
        pw = extract_keywords(rdf.loc[rdf["Sentiment"]=="Positive", text_column])
        nw = extract_keywords(rdf.loc[rdf["Sentiment"]=="Negative", text_column])
        fk = build_keywords_chart(pw, nw, POSITIVE_COLOR, NEGATIVE_COLOR)
        apply_theme(fk, title="Top Keywords", height=380, margin=dict(l=120), barmode="group")
        st.plotly_chart(fk, use_container_width=True, key="bulk_kw")
    except Exception:
        st.info("Keyword extraction unavailable.")

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

ft = build_trend_chart(pos, neg, neu, POSITIVE_COLOR, NEGATIVE_COLOR, NEUTRAL_COLOR)
apply_theme(ft, title="Sentiment Trend", height=350)
st.plotly_chart(ft, use_container_width=True, key="bulk_trend")

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── AI Summary (centralized) ──
with st.container():
    st.markdown('<div class="glass-card-header"><div class="section-title">🤖 AI Summary</div><div class="section-subtitle">Auto-generated insights from analysis results</div></div>', unsafe_allow_html=True)
    summary_html = generate_summary(rdf, sarcasm_on=sarcasm_was_on)
    st.markdown(f'<div style="color:#e8eaf6;line-height:2.0;margin-bottom:12px;font-size:0.92rem;">{summary_html}</div>', unsafe_allow_html=True)
    st.markdown('<span class="tag-pill tag-violet">AI-GENERATED</span> <span class="tag-pill tag-cyan">INSTANT</span>', unsafe_allow_html=True)
    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── Export (centralized) ──
render_export_buttons(rdf, filename_prefix="reviewsense_bulk")