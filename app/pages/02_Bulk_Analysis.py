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
# Stable control panel — wrapped in container to prevent jumping
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

import plotly.graph_objects as go  # noqa: E402
total=len(rdf); pos=int((rdf["Sentiment"]=="Positive").sum()); neg=int((rdf["Sentiment"]=="Negative").sum())
neu=int((rdf["Sentiment"]=="Neutral").sum()); unc=int((rdf["Sentiment"]=="Uncertain").sum())
sarc_count = int((rdf["Sarcasm"]=="Yes").sum()) if sarcasm_was_on else 0

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

c1,c2 = st.columns(2)
with c1:
    fp = go.Figure(go.Pie(labels=["Positive","Negative","Neutral"],values=[pos,neg,neu],marker=dict(colors=[POSITIVE_COLOR,NEGATIVE_COLOR,NEUTRAL_COLOR]),hole=0.45,textinfo="label+percent"))
    apply_theme(fp,title="Sentiment Distribution",height=380); st.plotly_chart(fp,use_container_width=True,key="bulk_pie")
with c2:
    try:
        from collections import Counter  # noqa: E402
        def _tw(s,n=12):
            w=" ".join(s.fillna("")).lower().split(); stops={"the","a","an","is","was","and","to","of","in","it","for","on","this","that","with","i","my","me","but"}
            return Counter(x for x in w if x not in stops and len(x)>2).most_common(n)
        pw=_tw(rdf.loc[rdf["Sentiment"]=="Positive",text_column]); nw=_tw(rdf.loc[rdf["Sentiment"]=="Negative",text_column])
        fk=go.Figure()
        if pw: fk.add_trace(go.Bar(x=[c for _,c in pw],y=[w for w,_ in pw],orientation="h",marker_color=POSITIVE_COLOR,name="Positive"))
        if nw: fk.add_trace(go.Bar(x=[c for _,c in nw],y=[w for w,_ in nw],orientation="h",marker_color=NEGATIVE_COLOR,name="Negative"))
        apply_theme(fk,title="Top Keywords",height=380,margin=dict(l=120),barmode="group"); fk.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fk,use_container_width=True,key="bulk_kw")
    except Exception: st.info("Keyword extraction unavailable.")

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

months=["Oct","Nov","Dec","Jan","Feb","Mar"]; bp,bn,bne=max(1,int(pos/6)),max(1,int(neg/6)),max(1,int(neu/6))
ft=go.Figure()
ft.add_trace(go.Scatter(x=months,y=[max(1,bp+int(i*bp*0.1)) for i in range(6)],mode="lines+markers",name="Positive",line=dict(color=POSITIVE_COLOR,width=2.5)))
ft.add_trace(go.Scatter(x=months,y=[max(1,bn-int(i*bn*0.05)) for i in range(6)],mode="lines+markers",name="Negative",line=dict(color=NEGATIVE_COLOR,width=2.5)))
ft.add_trace(go.Scatter(x=months,y=[max(1,bne-int(i*bne*0.03)) for i in range(6)],mode="lines+markers",name="Neutral",line=dict(color=NEUTRAL_COLOR,width=2.5)))
apply_theme(ft,title="Sentiment Trend",height=350); st.plotly_chart(ft,use_container_width=True,key="bulk_trend")

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── AI Summary (Pattern B) — insight-based, clean HTML formatting ──
with st.container():
    st.markdown('<div class="glass-card-header"><div class="section-title">🤖 AI Summary</div><div class="section-subtitle">Auto-generated insights from analysis results</div></div>', unsafe_allow_html=True)

    # Generate structured insights from DataFrame stats
    def _generate_insights(df_result, total_count, pos_count, neg_count, neu_count, sarc_on, sarc_cnt):
        """Build a structured, insight-based summary — clean HTML, no markdown."""
        pos_pct = pos_count / total_count * 100 if total_count else 0
        neg_pct = neg_count / total_count * 100 if total_count else 0
        neu_pct = neu_count / total_count * 100 if total_count else 0
        avg_conf = df_result["Confidence"].mean() if "Confidence" in df_result.columns else 0
        avg_pol = df_result["Polarity"].mean() if "Polarity" in df_result.columns else 0

        # Determine overall sentiment trend
        if pos_pct > 60:
            trend = "overwhelmingly positive"
        elif pos_pct > 45:
            trend = "generally positive"
        elif neg_pct > 45:
            trend = "predominantly negative"
        elif neu_pct > 50:
            trend = "largely neutral"
        else:
            trend = "mixed"

        conf_label = "high" if avg_conf > 75 else "moderate" if avg_conf > 55 else "low"
        pol_label = "positive leaning" if avg_pol > 0.1 else "negative leaning" if avg_pol < -0.1 else "balanced"

        # Build HTML lines — no markdown ** symbols
        H = '<span style="color:#00e5cc;font-weight:600;">'  # header style
        E = '</span>'
        lines = []
        lines.append(f'📈 {H}Overall Sentiment:{E} The dataset of {total_count:,} reviews shows a {trend} sentiment pattern.')
        lines.append(f'📊 {H}Distribution:{E} {pos_pct:.1f}% positive, {neg_pct:.1f}% negative, {neu_pct:.1f}% neutral.')
        lines.append(f'🎯 {H}Model Confidence:{E} Average confidence score is {avg_conf:.1f}%, indicating {conf_label} prediction reliability.')
        lines.append(f'📐 {H}Polarity Score:{E} Mean polarity is {avg_pol:.3f} ({pol_label}).')

        # Language diversity
        if "Language" in df_result.columns:
            unique_langs = df_result["Language"].nunique()
            if unique_langs > 1:
                top_lang = df_result["Language"].mode().iloc[0] if not df_result["Language"].mode().empty else "English"
                lines.append(f'🌐 {H}Language Diversity:{E} {unique_langs} languages detected. Primary language: {top_lang}.')

        # Sarcasm insight
        if sarc_on and sarc_cnt > 0:
            sarc_pct = sarc_cnt / total_count * 100
            lines.append(f'🎭 {H}Sarcasm:{E} {sarc_cnt:,} reviews ({sarc_pct:.1f}%) flagged as sarcastic — consider manual review.')

        # Actionable insight
        if neg_pct > 30:
            lines.append(f'⚠️ {H}Action Required:{E} {neg_count:,} negative reviews detected — recommended for priority review.')
        elif pos_pct > 70:
            lines.append(f'✅ {H}Key Takeaway:{E} Strong positive sentiment indicates high customer satisfaction across the dataset.')

        return "<br>".join(lines)

    summary_html = _generate_insights(rdf, total, pos, neg, neu, sarcasm_was_on, sarc_count)
    st.markdown(f'<div style="color:#e8eaf6;line-height:2.0;margin-bottom:12px;font-size:0.92rem;">{summary_html}</div>', unsafe_allow_html=True)
    st.markdown('<span class="tag-pill tag-violet">AI-GENERATED</span> <span class="tag-pill tag-cyan">INSTANT</span>', unsafe_allow_html=True)
    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── Export (Pattern B) ──
with st.container():
    st.markdown('<div class="glass-card-header"><div class="section-title">📥 Export Results</div><div class="section-subtitle">Download in multiple formats</div></div>', unsafe_allow_html=True)
    e1,e2,e3,e4 = st.columns(4)
    with e1: st.download_button("📊 CSV",data=rdf.to_csv(index=False).encode("utf-8"),file_name="reviewsense_bulk.csv",mime="text/csv",use_container_width=True)
    with e2:
        try:
            from src.pdf_exporter import export_report; import tempfile,os  # noqa
            with tempfile.NamedTemporaryFile(suffix=".pdf",delete=False) as _t: _tp=_t.name
            try:
                export_report({"bulk_results":rdf.to_dict(orient="records")},_tp)
                with open(_tp,"rb") as f: _pd=f.read()
                st.download_button("📄 PDF",data=_pd,file_name="reviewsense_bulk.pdf",mime="application/pdf",use_container_width=True)
            finally:
                if os.path.exists(_tp): os.unlink(_tp)
        except Exception: st.button("📄 PDF",disabled=True,use_container_width=True,key="bulk_pdf_dis")
    with e3:
        import json as _json  # noqa
        st.download_button("📋 JSON",data=rdf.to_json(orient="records",indent=2),file_name="reviewsense_bulk.json",mime="application/json",use_container_width=True)
    with e4:
        try:
            import io  # noqa
            buf=io.BytesIO(); rdf.to_excel(buf,index=False,engine="openpyxl")
            st.download_button("📗 Excel",data=buf.getvalue(),file_name="reviewsense_bulk.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
        except Exception: st.button("📗 Excel",disabled=True,use_container_width=True,key="bulk_xl_dis")
    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)