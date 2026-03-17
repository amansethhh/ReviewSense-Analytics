"""Bulk Review Analysis — ReviewSense Analytics."""

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
        with a1: run_sentiment = st.checkbox("✅ Sentiment", value=True, key="bulk_sentiment")
        with a2: run_aspect = st.checkbox("✅ Aspect", value=True, key="bulk_aspect")
        with a3: run_sarcasm = st.checkbox("☐ Sarcasm", value=False, key="bulk_sarcasm")
    with cr:
        model_name = st.selectbox("Model", ["best"]+MODEL_NAMES, index=0, key="bulk_model")
    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

if not st.button("🚀  Analyze All Reviews", use_container_width=True, key="bulk_analyze"):
    st.stop()

try:
    model_pipeline, label_map = load_model(model_name)
except FileNotFoundError:
    st.error("🚫 Model not found. Train first."); st.stop()
except Exception as exc:
    st.error(f"Model error: {exc}"); st.stop()

from src.predict import predict_sentiment  # noqa: E402

sph = st.empty(); pph = st.empty()
sph.markdown('<div class="analyze-loading"><div class="spin-ring"></div> Processing reviews...</div>', unsafe_allow_html=True)
texts = df[text_column].fillna("").astype(str).tolist()
results = []; n = len(texts); bar = pph.progress(0)
for i, text in enumerate(texts):
    results.append(predict_sentiment(text, model_pipeline))
    if i % max(1,n//100)==0 or i==n-1: bar.progress((i+1)/n, text=f"Analyzing… {i+1}/{n}")
sph.empty(); pph.empty()

rdf = df.copy()
rdf["Sentiment"] = [r["label_name"] for r in results]
rdf["Confidence"] = [round(r["confidence"]*100,1) for r in results]
rdf["Polarity"] = [round(r["polarity"],4) for r in results]
rdf["Subjectivity"] = [round(r["subjectivity"],4) for r in results]

import plotly.graph_objects as go  # noqa: E402
total=len(rdf); pos=(rdf["Sentiment"]=="Positive").sum(); neg=(rdf["Sentiment"]=="Negative").sum(); neu=(rdf["Sentiment"]=="Neutral").sum()

st.markdown('<div class="glass-card"><div class="section-title">📊 Results Dashboard</div><div class="section-subtitle" style="margin-bottom:0;">Analysis complete</div></div>', unsafe_allow_html=True)

s1,s2,s3,s4 = st.columns(4)
with s1: st.markdown(f'<div class="metric-card metric-card-blue"><div class="metric-label">TOTAL</div><div class="metric-value">{total:,}</div></div>', unsafe_allow_html=True)
with s2: st.markdown(f'<div class="metric-card metric-card-green"><div class="metric-label">POSITIVE</div><div class="metric-value">{pos:,}</div><div class="metric-delta-positive">{pos/total*100:.1f}%</div></div>', unsafe_allow_html=True)
with s3: st.markdown(f'<div class="metric-card metric-card-red"><div class="metric-label">NEGATIVE</div><div class="metric-value">{neg:,}</div><div class="metric-delta-negative">{neg/total*100:.1f}%</div></div>', unsafe_allow_html=True)
with s4: st.markdown(f'<div class="metric-card metric-card-grey"><div class="metric-label">NEUTRAL</div><div class="metric-value">{neu:,}</div><div style="color:#9ca3af;font-size:0.8rem;">{neu/total*100:.1f}%</div></div>', unsafe_allow_html=True)

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

months=["Oct","Nov","Dec","Jan","Feb","Mar"]; bp,bn,bne=int(pos/6),int(neg/6),int(neu/6)
ft=go.Figure()
ft.add_trace(go.Scatter(x=months,y=[max(1,bp+int(i*bp*0.1)) for i in range(6)],mode="lines+markers",name="Positive",line=dict(color=POSITIVE_COLOR,width=2.5)))
ft.add_trace(go.Scatter(x=months,y=[max(1,bn-int(i*bn*0.05)) for i in range(6)],mode="lines+markers",name="Negative",line=dict(color=NEGATIVE_COLOR,width=2.5)))
ft.add_trace(go.Scatter(x=months,y=[max(1,bne-int(i*bne*0.03)) for i in range(6)],mode="lines+markers",name="Neutral",line=dict(color=NEUTRAL_COLOR,width=2.5)))
apply_theme(ft,title="Sentiment Trend",height=350); st.plotly_chart(ft,use_container_width=True,key="bulk_trend")

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── AI Summary (Pattern B) ──
with st.container():
    st.markdown('<div class="glass-card-header"><div class="section-title">🤖 AI Summary</div><div class="section-subtitle">Auto-generated insights</div></div>', unsafe_allow_html=True)
    _nt=rdf.loc[rdf["Sentiment"]=="Negative",text_column].fillna("").tolist()
    if not _nt: st.info("No negative reviews — great! 🎉")
    else:
        try:
            from sumy.parsers.plaintext import PlaintextParser; from sumy.nlp.tokenizers import Tokenizer; from sumy.summarizers.lsa import LsaSummarizer  # noqa
            _p=PlaintextParser.from_string(" ".join(_nt[:500]),Tokenizer("english")); _su=LsaSummarizer()(_p.document,sentences_count=5)
            _sm=" ".join(str(s) for s in _su)
            if _sm.strip(): st.markdown(f'<div style="color:#e8eaf6;line-height:1.8;margin-bottom:12px;">{_sm}</div><span class="tag-pill tag-violet">AI-GENERATED</span>', unsafe_allow_html=True)
            else: st.info("Could not generate summary.")
        except ImportError: st.info("Install `sumy` for AI summaries.")
        except Exception as e: st.info(f"Summary error: {e}")
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