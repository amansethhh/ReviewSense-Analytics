"""Multilingual Sentiment Analysis — ReviewSense Analytics."""

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

st.set_page_config(page_title="Language Analysis — ReviewSense", page_icon="🌐", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
html,body,[data-testid="stApp"],[data-testid="stAppViewContainer"],
[data-testid="stMain"],.main,.block-container{background-color:#070b14!important;background:#070b14!important}
[data-testid="stSidebarNav"],[data-testid="stSidebarNav"] *{display:none!important}
</style>""", unsafe_allow_html=True)

from ui.sidebar import load_css, render_sidebar  # noqa: E402
from ui.theme import apply_theme, POSITIVE_COLOR, NEGATIVE_COLOR, NEUTRAL_COLOR  # noqa: E402
from src.config import MODEL_NAMES  # noqa: E402
from src.analytics import compute_metrics, generate_summary, generate_summary_single, extract_keywords, extract_keywords_single, build_sentiment_pie, build_keywords_chart, build_trend_chart  # noqa: E402
from src.exporter import render_export_buttons  # noqa: E402


load_css()
render_sidebar()

# ━━━ SESSION STATE ━━━
for _key, _default in [
    ("lang_single_result", None),
    ("lang_single_text", ""),
    ("lang_batch_results_df", None),
    ("lang_batch_raw_results", None),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ━━━ HEADER (Pattern A) ━━━
st.markdown("""<div class="glass-card">
  <div class="section-title">🌐 Multilingual Sentiment Analysis</div>
  <div class="section-subtitle" style="margin-bottom:0;">Detect language, translate to English, and run sentiment analysis — all in one step.</div>
</div>""", unsafe_allow_html=True)

# ━━━ SUPPORTED LANGUAGES — CSS gradient flag boxes ━━━
st.markdown('<div class="section-title">🗺️ Supported Languages</div><div class="section-subtitle">Auto-detection across 50+ languages</div>', unsafe_allow_html=True)

languages_row1 = [
    ("gb", "English", "EN"),
    ("in", "Hindi", "HI"),
    ("es", "Spanish", "ES"),
    ("fr", "French", "FR"),
    ("de", "German", "DE"),
    ("cn", "Chinese", "CN"),
    ("jp", "Japanese", "JP"),
    ("sa", "Arabic", "SA"),
]

languages_row2 = [
    ("pt", "Portuguese", "PT"),
    ("ru", "Russian", "RU"),
    ("kr", "Korean", "KR"),
    ("it", "Italian", "IT"),
    ("tr", "Turkish", "TR"),
    ("id", "Indonesian", "ID"),
    ("th", "Thai", "TH"),
    ("vn", "Vietnamese", "VN"),
]

for row_langs in (languages_row1, languages_row2):
    cols = st.columns(8)
    for i, (flag_cls, name, iso) in enumerate(row_langs):
        with cols[i]:
            st.markdown(f"""<div class="lang-tile">
              <div class="flag-box flag-{flag_cls}">{iso}</div>
              <div class="lang-name">{name}</div>
              <div class="lang-iso">{iso}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━ ANALYZE TEXT (Pattern B — unified card) ━━━
with st.container():
    st.markdown("""<div class="glass-card-header">
      <div class="section-title">✏️ Analyze Text</div>
      <div class="section-subtitle">Enter text in any language for detection and analysis</div>
      <span style="color:#22c55e;font-size:0.8rem;font-weight:600;">● Auto-detect enabled</span>
    </div>""", unsafe_allow_html=True)

    lang_input_text = st.text_area("Review Text (any language)",
        value="La batterie dure longtemps, mais l'écran est trop sombre.",
        height=120, key="lang_input", label_visibility="collapsed")

    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

analyze_btn = st.button("🌐  Detect & Analyze", use_container_width=True, key="lang_analyze")
st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━ SINGLE ANALYSIS ━━━
if analyze_btn:
    if not lang_input_text.strip():
        st.warning("Please enter some text."); st.stop()

    sph = st.empty(); pph = st.empty()
    sph.markdown('<div class="analyze-loading"><div class="spin-ring"></div><div><div style="font-weight:600;color:#93c5fd;">Detecting language...</div><div style="font-size:0.75rem;color:#7986cb;margin-top:2px;">Auto-detect · Translate · Analyze</div></div></div>', unsafe_allow_html=True)
    bar = pph.progress(0)
    for pct in [15,35,55]: time.sleep(0.12); bar.progress(pct)

    from src.pipeline.inference import run_pipeline  # noqa: E402
    result = run_pipeline(lang_input_text, enable_sarcasm=False, enable_aspects=False)

    for pct in [70, 85]: time.sleep(0.1); bar.progress(pct)
    bar.progress(100); time.sleep(0.08); sph.empty(); pph.empty()

    st.session_state.lang_single_result = result
    st.session_state.lang_single_text = lang_input_text

# ── Render single results from session state (anti-flicker) ──
result = st.session_state.lang_single_result
if result is not None:
    lang_input_text = st.session_state.lang_single_text
    detected_lang = result["language"]
    lang_name = result["language_name"]
    flag_emoji = result["flag_emoji"]
    translated = result["translated"]
    was_translated = result["was_translated"]
    label_name = result["sentiment"]
    confidence = result["confidence"]
    polarity = result["polarity"]
    subjectivity = result["subjectivity"]

    # ── Detection + Sentiment (2-col, Pattern A) ──
    d1, d2 = st.columns(2)
    with d1:
        ts = ""
        if was_translated:
            ts = f'<div style="margin-top:16px;padding-top:12px;border-top:1px solid rgba(59,130,246,0.1);"><div style="color:#7986cb;font-size:0.75rem;margin-bottom:8px;">Translated:</div><div style="color:#e8eaf6;font-size:0.9rem;line-height:1.6;background:rgba(13,17,23,0.5);padding:12px;border-radius:8px;">{translated}</div><span class="tag-pill tag-teal" style="margin-top:8px;">GoogleTrans</span></div>'
        st.markdown(f"""<div class="glass-card">
          <div class="section-title">🔍 Detected Language</div>
          <div style="display:flex;align-items:center;gap:12px;margin-top:12px;">
            <span style="font-size:2.5rem;">{flag_emoji}</span>
            <div><div style="font-size:1.4rem;font-weight:700;color:#e8eaf6;">{lang_name}</div>
            <div style="display:flex;gap:6px;margin-top:4px;"><span class="tag-pill tag-cyan">{detected_lang.upper()}</span><span class="tag-pill tag-green">HIGH CONFIDENCE</span></div></div>
          </div>{ts}
        </div>""", unsafe_allow_html=True)

    with d2:
        bc = {"Positive":"badge-positive","Negative":"badge-negative","Neutral":"badge-neutral"}.get(label_name,"badge-neutral")
        bd = {"Positive":"✅ Positive","Negative":"❌ Negative","Neutral":"◼ Neutral"}.get(label_name,label_name)
        st.markdown(f"""<div class="glass-card">
          <div class="section-title">📊 Sentiment Result</div>
          <div style="margin-top:16px;margin-bottom:20px;"><span class="{bc}" style="font-size:1.3rem;padding:10px 28px;">{bd}</span></div>
        </div>""", unsafe_allow_html=True)

    # ── 3-Column Metrics ──
    mcol1, mcol2, mcol3 = st.columns(3)
    with mcol1:
        st.markdown(f'<div class="metric-card metric-card-cyan"><div class="metric-label">CONFIDENCE</div><div class="metric-value">{confidence*100:.1f}%</div></div>', unsafe_allow_html=True)
    with mcol2:
        st.markdown(f'<div class="metric-card metric-card-violet"><div class="metric-label">POLARITY</div><div class="metric-value">{polarity:.3f}</div></div>', unsafe_allow_html=True)
    with mcol3:
        st.markdown(f'<div class="metric-card metric-card-amber"><div class="metric-label">SUBJECTIVITY</div><div class="metric-value">{subjectivity:.3f}</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── Pipeline (Pattern A) ──
    st.markdown('<div class="section-title">🔄 Processing Pipeline</div>', unsafe_allow_html=True)
    steps = [("📥","Input","Raw text"),("🔍","Detect","Language ID"),("🌐","Translate","To English"),("🧠","Analyze","NLP Model"),("📊","Result","Sentiment")]
    pp = st.columns(len(steps)*2-1)
    for si,(icon,label,sub) in enumerate(steps):
        with pp[si*2]:
            st.markdown(f'<div class="pipeline-step completed"><div class="pipeline-icon">{icon}</div><div class="pipeline-label">{label}</div><div class="pipeline-sublabel">{sub}</div></div>', unsafe_allow_html=True)
        if si < len(steps)-1:
            with pp[si*2+1]:
                st.markdown('<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#3b82f6;font-size:1.2rem;">→</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── Keyword Extraction (NEW) ──
    with st.container():
        st.markdown('<div class="glass-card-header"><div class="section-title">🔑 Keyword Extraction</div><div class="section-subtitle">Key terms detected in the review</div></div>', unsafe_allow_html=True)
        analysis_text = translated if was_translated else lang_input_text
        kw = extract_keywords_single(analysis_text, n=8)
        if kw:
            kw_html = " ".join(f'<span class="tag-pill tag-cyan" style="margin:2px;">{w} ({c})</span>' for w, c in kw)
            st.markdown(f'<div style="padding:8px 0;">{kw_html}</div>', unsafe_allow_html=True)
        else:
            st.info("No significant keywords detected.")
        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── AI Micro-Summary (NEW) ──
    with st.container():
        st.markdown('<div class="glass-card-header"><div class="section-title">🤖 AI Summary</div><div class="section-subtitle">Single review insight</div></div>', unsafe_allow_html=True)
        summary_html = generate_summary_single(result)
        st.markdown(f'<div style="color:#e8eaf6;line-height:2.0;margin-bottom:12px;font-size:0.92rem;">{summary_html}</div>', unsafe_allow_html=True)
        st.markdown('<span class="tag-pill tag-violet">AI-GENERATED</span> <span class="tag-pill tag-cyan">INSTANT</span>', unsafe_allow_html=True)
        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── LIME (Pattern B) ──
    with st.container():
        st.markdown('<div class="glass-card-header"><div class="section-title">🔍 Word-Level Explanation</div><div class="section-subtitle">LIME on translated text · Cached for speed</div></div>', unsafe_allow_html=True)
        try:
            from src.lime_explainer import explain_prediction, highlight_text_html  # noqa: E402
            import plotly.graph_objects as go  # noqa: E402
            analysis_text = translated if was_translated else lang_input_text

            lime_ph = st.empty()
            lime_ph.info("⏳ Generating LIME explanation... (cached after first run)")
            ww = explain_prediction(analysis_text, num_features=6)
            lime_ph.empty()

            st.markdown(highlight_text_html(analysis_text, ww), unsafe_allow_html=True)
            if ww:
                ws=[w for w,_ in ww]; wts=[v for _,v in ww]
                cl=[POSITIVE_COLOR if v>=0 else NEGATIVE_COLOR for v in wts]
                fig=go.Figure(go.Bar(x=wts,y=ws,orientation="h",marker_color=cl))
                apply_theme(fig,title="",height=350,margin=dict(l=120))
                fig.update_layout(xaxis_title="← Negative | Positive →",yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig,use_container_width=True,key="lang_lime")
        except Exception as e:
            st.info(f"LIME unavailable: {e}")
        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── Export (centralized, 4-format) (NEW) ──
    import pandas as pd  # noqa: E402
    single_df = pd.DataFrame([{
        "Text": lang_input_text,
        "Language": lang_name,
        "Translated": translated,
        "Sentiment": label_name,
        "Confidence": round(confidence * 100, 1),
        "Polarity": round(polarity, 4),
        "Subjectivity": round(subjectivity, 4),
    }])
    render_export_buttons(single_df, filename_prefix="reviewsense_lang_single")

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━ BATCH UPLOAD (unified Pattern B) ━━━
st.markdown('<div class="section-title">📂 Batch Language Analysis</div><div class="section-subtitle">Upload CSV with non-English reviews</div>', unsafe_allow_html=True)

with st.container():
    st.markdown("""<div class="glass-card-header">
      <div class="upload-zone-header">
        <div class="upload-icon-circle">🌐</div>
        <div><div class="upload-text-primary">Upload multilingual review dataset</div>
        <div class="upload-text-secondary">Auto-detects language for each row</div></div>
      </div>
      <div class="upload-badges">
        <span class="upload-badge upload-badge-csv">CSV</span>
        <span class="upload-badge upload-badge-limit">Max 200MB</span>
        <span class="upload-badge upload-badge-limit">50+ Languages</span>
      </div>
    </div>""", unsafe_allow_html=True)
    batch_file = st.file_uploader("", type=["csv"], label_visibility="collapsed", key="lang_batch_upload")
    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

if batch_file is not None:
    import pandas as pd  # noqa: E402
    try:
        bdf = pd.read_csv(batch_file)
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}"); st.stop()

    st.dataframe(bdf.head(5), use_container_width=True)

    _TH=("text","review","comment","sentence","content")
    _sc=[c for c in bdf.columns if bdf[c].dtype==object]
    _ac=next((c for h in _TH for c in _sc if h in c.lower()),_sc[0] if _sc else bdf.columns[0])

    with st.container():
        st.markdown('<div class="glass-card-header"><div class="section-title">⚙️ Batch Settings</div><div class="section-subtitle">Select text column</div></div>', unsafe_allow_html=True)
        btc = st.selectbox("Text column:", options=bdf.columns.tolist(), index=bdf.columns.tolist().index(_ac), key="lang_batch_col")
        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    if st.button("🌐  Translate & Analyze All", use_container_width=True, key="lang_batch_btn"):
        from src.pipeline.inference import run_pipeline_batch as rpb  # noqa: E402

        bsph = st.empty()
        bsph.markdown('<div class="analyze-loading"><div class="spin-ring"></div> Translating and analyzing with RoBERTa...</div>', unsafe_allow_html=True)
        texts = bdf[btc].fillna("").astype(str).tolist()
        prog = st.progress(0)
        lang_status = st.empty()

        # Synchronized progress callback
        def _lang_progress(pct, msg):
            prog.progress(min(pct, 100), text=msg)
            lang_status.markdown(f"**{msg}**")

        batch_results = rpb(texts, enable_sarcasm=False, enable_aspects=False, progress_callback=_lang_progress)

        prog.progress(100, text="✅ Complete!")
        import time; time.sleep(0.3)  # noqa: E702
        bsph.empty(); prog.empty()
        lang_status.success("✅ Analysis complete")

        # Build results DataFrame
        br = []
        for r in batch_results:
            orig = r["original"]
            br.append({
                "Original": orig[:80] + ("…" if len(orig) > 80 else ""),
                "Language": f"{r['flag_emoji']} {r['language_name']}",
                "Translated": r["translated"][:80] + ("…" if len(r["translated"]) > 80 else ""),
                "Sentiment": r["sentiment"],
                "Confidence": round(r["confidence"] * 100, 1),
                "Polarity": round(r["polarity"], 4),
                "Subjectivity": round(r["subjectivity"], 4),
            })
        odf = pd.DataFrame(br)

        # Persist in session state
        st.session_state.lang_batch_results_df = odf
        st.session_state.lang_batch_raw_results = batch_results

    # ── Render batch results from session state (anti-flicker) ──
    odf = st.session_state.lang_batch_results_df
    if odf is not None:
        import plotly.graph_objects as go  # noqa: E402

        st.dataframe(odf, use_container_width=True)
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        # ── Language Distribution Chart ──
        with st.container():
            st.markdown('<div class="glass-card-header"><div class="section-title">📊 Language Distribution</div><div class="section-subtitle">Detected languages</div></div>', unsafe_allow_html=True)
            lc=odf["Language"].value_counts(); tl=lc.sum()
            fl=go.Figure(go.Bar(x=lc.values,y=lc.index,orientation="h",marker=dict(color=lc.values,colorscale=[[0,"#0d4a6b"],[1,"#00e5cc"]]),text=[f"{v/tl*100:.1f}%" for v in lc.values],textposition="auto"))
            apply_theme(fl,title="",height=max(250,len(lc)*45),margin=dict(l=140))
            st.plotly_chart(fl,use_container_width=True,key="lang_dist")
            st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

        # ── Results Dashboard (NEW — feature parity with Bulk) ──
        # Build a temp df with Sentiment column for compute_metrics
        metrics = compute_metrics(odf)
        total, pos, neg, neu = metrics["total"], metrics["pos"], metrics["neg"], metrics["neu"]

        k1,k2,k3,k4,k5 = st.columns(5)
        ul = odf["Language"].nunique()
        with k1: st.markdown(f'<div class="metric-card metric-card-cyan"><div class="metric-label">TOTAL REVIEWS</div><div class="metric-value">{total:,}</div></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="metric-card metric-card-green"><div class="metric-label">POSITIVE</div><div class="metric-value">{pos:,}</div></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="metric-card metric-card-red"><div class="metric-label">NEGATIVE</div><div class="metric-value">{neg:,}</div></div>', unsafe_allow_html=True)
        with k4: st.markdown(f'<div class="metric-card metric-card-grey"><div class="metric-label">NEUTRAL</div><div class="metric-value">{neu:,}</div></div>', unsafe_allow_html=True)
        with k5: st.markdown(f'<div class="metric-card metric-card-teal"><div class="metric-label">LANGUAGES</div><div class="metric-value">{ul}</div></div>', unsafe_allow_html=True)

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        # ── Sentiment Pie + Keywords (NEW) ──
        ch1, ch2 = st.columns(2)
        with ch1:
            fp = build_sentiment_pie(pos, neg, neu, POSITIVE_COLOR, NEGATIVE_COLOR, NEUTRAL_COLOR)
            apply_theme(fp, title="Sentiment Distribution", height=380)
            st.plotly_chart(fp, use_container_width=True, key="lang_batch_pie")
        with ch2:
            try:
                pw = extract_keywords(odf.loc[odf["Sentiment"]=="Positive", "Translated"])
                nw = extract_keywords(odf.loc[odf["Sentiment"]=="Negative", "Translated"])
                fk = build_keywords_chart(pw, nw, POSITIVE_COLOR, NEGATIVE_COLOR)
                apply_theme(fk, title="Top Keywords", height=380, margin=dict(l=120), barmode="group")
                st.plotly_chart(fk, use_container_width=True, key="lang_batch_kw")
            except Exception:
                st.info("Keyword extraction unavailable.")

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        # ── Sentiment Trend (NEW) ──
        ft = build_trend_chart(pos, neg, neu, POSITIVE_COLOR, NEGATIVE_COLOR, NEUTRAL_COLOR)
        apply_theme(ft, title="Sentiment Trend", height=350)
        st.plotly_chart(ft, use_container_width=True, key="lang_batch_trend")

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        # ── AI Summary (NEW) ──
        with st.container():
            st.markdown('<div class="glass-card-header"><div class="section-title">🤖 AI Summary</div><div class="section-subtitle">Auto-generated insights from batch analysis</div></div>', unsafe_allow_html=True)
            summary_html = generate_summary(odf)
            st.markdown(f'<div style="color:#e8eaf6;line-height:2.0;margin-bottom:12px;font-size:0.92rem;">{summary_html}</div>', unsafe_allow_html=True)
            st.markdown('<span class="tag-pill tag-violet">AI-GENERATED</span> <span class="tag-pill tag-cyan">INSTANT</span>', unsafe_allow_html=True)
            st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        # ── Export (centralized, 4-format — upgraded from 3) ──
        render_export_buttons(odf, filename_prefix="reviewsense_multilingual")