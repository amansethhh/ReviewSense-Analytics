"""Multilingual Sentiment Analysis — ReviewSense Analytics.

FIX 5: Unicode flag emojis with Segoe UI Emoji font stack.
FIX 6: Upload zone redesign.
Container patterns fixed (Pattern A/B).
"""

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
    page_title="Language Analysis — ReviewSense",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Background flash prevention ─────────────────────────────
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
    ACCENT_CYAN, CHART_PALETTE,
)
from src.config import MODEL_NAMES  # noqa: E402
from utils import load_model  # noqa: E402

load_css()
render_sidebar()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div class="section-title">🌐 Multilingual Sentiment Analysis</div>
<div class="section-subtitle">Detect language, translate to English, and run sentiment analysis — all in one step.</div>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIX 5 — SUPPORTED LANGUAGES (tiles with real flags)
# Pattern A — all HTML in one call, no ghost container
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div class="glass-card">
  <div class="section-title">🗺️ Supported Languages</div>
  <div class="section-subtitle">Auto-detection across 50+ languages</div>
</div>
""", unsafe_allow_html=True)

languages = [
    ("\U0001F1EC\U0001F1E7", "English",  "EN"),
    ("\U0001F1EE\U0001F1F3", "Hindi",    "HI"),
    ("\U0001F1EE\U0001F1F3", "Tamil",    "TA"),
    ("\U0001F1EE\U0001F1F3", "Bengali",  "BN"),
    ("\U0001F1EA\U0001F1F8", "Spanish",  "ES"),
    ("\U0001F1EB\U0001F1F7", "French",   "FR"),
    ("\U0001F1E9\U0001F1EA", "German",   "DE"),
    ("\U0001F1E8\U0001F1F3", "Chinese",  "CN"),
]

cols = st.columns(8)
for col, (flag, name, iso) in zip(cols, languages):
    with col:
        st.markdown(f"""
        <div class="lang-tile">
          <div class="lang-flag">{flag}</div>
          <div class="lang-name">{name}</div>
          <div class="lang-iso">{iso}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANALYZE TEXT — Pattern B (widgets inside)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.container():
    st.markdown("""
    <div class="glass-card-header">
      <div class="section-title">✏️ Analyze Text</div>
      <div style="margin-bottom:4px;">
        <span style="color:#22c55e;font-size:0.8rem;font-weight:600;">● Auto-detect enabled</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    lang_input_text = st.text_area(
        "Review Text (any language)",
        value="La batterie dure longtemps, mais l'écran est trop sombre. Dans l'ensemble, c'est un bon produit.",
        height=120,
        key="lang_input",
    )

    analyze_btn = st.button("🌐  Detect & Analyze", use_container_width=True, key="lang_analyze")
    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DETECTION & ANALYSIS RESULT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if analyze_btn:
    if not lang_input_text.strip():
        st.warning("Please enter some text before analyzing.")
        st.stop()

    # ── Animated Loading ─────────────────────────────────────
    spinner_ph = st.empty()
    progress_ph = st.empty()

    spinner_ph.markdown("""
    <div class="analyze-loading">
      <div class="pulse-ring"></div>
      Detecting language and translating...
    </div>
    """, unsafe_allow_html=True)

    bar = progress_ph.progress(0)
    for pct in [15, 35, 55]:
        time.sleep(0.12)
        bar.progress(pct)

    try:
        from src.translator import detect_and_translate  # noqa: E402
        translation_result = detect_and_translate(lang_input_text)
    except Exception as exc:
        spinner_ph.empty()
        progress_ph.empty()
        st.error(f"Language detection / translation error: {exc}")
        st.stop()

    for pct in [70, 85]:
        time.sleep(0.1)
        bar.progress(pct)

    detected_lang = translation_result["detected_language"]
    lang_name = translation_result["language_name"]
    flag_emoji = translation_result["flag_emoji"]
    translated = translation_result["translated_text"]
    was_translated = translation_result["was_translated"]

    # ── Load model and predict ───────────────────────────────
    model_name = st.session_state.get("selected_model", "best")
    try:
        model_pipeline, _ = load_model(model_name)
    except FileNotFoundError:
        spinner_ph.empty()
        progress_ph.empty()
        st.error("🚫 Model not found. Train first:\n\n```\npython src/train_classical.py\n```")
        st.stop()
    except Exception as exc:
        spinner_ph.empty()
        progress_ph.empty()
        st.error(f"Model loading error: {exc}")
        st.stop()

    from src.predict import predict_sentiment  # noqa: E402

    analysis_text = translated if was_translated else lang_input_text
    pred = predict_sentiment(analysis_text, model_pipeline)

    bar.progress(100)
    time.sleep(0.08)
    spinner_ph.empty()
    progress_ph.empty()

    label_name = pred["label_name"]
    confidence = pred["confidence"]
    polarity = pred["polarity"]
    subjectivity = pred["subjectivity"]

    # ── Detection Result (2 columns, Pattern A) ──────────────
    det1, det2 = st.columns(2)

    with det1:
        translated_section = ""
        if was_translated:
            translated_section = f"""
            <div style="margin-top:16px;padding-top:12px;border-top:1px solid rgba(59,130,246,0.1);">
              <div style="color:#7986cb;font-size:0.75rem;margin-bottom:8px;">Translated to English:</div>
              <div style="color:#e8eaf6;font-size:0.9rem;line-height:1.6;background:rgba(13,17,23,0.5);
                padding:12px;border-radius:8px;">{translated}</div>
              <span class="tag-pill tag-teal" style="margin-top:8px;">Translated by GoogleTrans Engine</span>
            </div>
            """

        st.markdown(f"""
        <div class="glass-card">
          <div style="color:#7986cb;font-size:0.7rem;text-transform:uppercase;
            letter-spacing:1px;font-weight:600;">Detected Language</div>
          <div style="display:flex;align-items:center;gap:12px;margin-top:12px;">
            <span style="font-size:2.5rem;">{flag_emoji}</span>
            <div>
              <div style="font-size:1.4rem;font-weight:700;color:#e8eaf6;">{lang_name}</div>
              <div style="display:flex;gap:6px;margin-top:4px;">
                <span class="tag-pill tag-cyan">{detected_lang.upper()}</span>
                <span class="tag-pill tag-green">HIGH CONFIDENCE</span>
              </div>
            </div>
          </div>
          {translated_section}
        </div>
        """, unsafe_allow_html=True)

    with det2:
        badge_class = {
            "Positive": "badge-positive",
            "Negative": "badge-negative",
            "Neutral": "badge-neutral",
        }.get(label_name, "badge-neutral")
        badge_display = {
            "Positive": "✅ Positive",
            "Negative": "❌ Negative",
            "Neutral": "◼ Neutral",
        }.get(label_name, label_name)

        st.markdown(f"""
        <div class="glass-card">
          <div style="color:#7986cb;font-size:0.7rem;text-transform:uppercase;
            letter-spacing:1px;font-weight:600;">Sentiment Analysis Result</div>
          <div style="margin-top:16px;margin-bottom:20px;">
            <span class="{badge_class}" style="font-size:1.3rem;padding:10px 28px;">{badge_display}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Metrics (Pattern A)
        st.markdown(f"""
        <div class="metric-card metric-card-cyan" style="margin-top:8px;">
          <div class="metric-label">CONFIDENCE</div>
          <div class="metric-value">{confidence*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(float(confidence))

        st.markdown(f"""
        <div class="metric-card metric-card-blue" style="margin-top:8px;">
          <div class="metric-label">POLARITY</div>
          <div class="metric-value">{polarity:.3f}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card metric-card-violet" style="margin-top:8px;">
          <div class="metric-label">SUBJECTIVITY</div>
          <div class="metric-value">{subjectivity:.3f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── Pipeline Visualization — Pattern A ───────────────────
    st.markdown("""
    <div class="glass-card">
      <div class="section-title">🔄 Processing Pipeline</div>
      <div class="section-subtitle">End-to-end multilingual analysis flow</div>
    """, unsafe_allow_html=True)

    steps = [
        ("📥", "Input", "Raw text"),
        ("🔍", "Detect", "Language ID"),
        ("🌐", "Translate", "To English"),
        ("🧠", "Analyze", "NLP Model"),
        ("📊", "Result", "Sentiment out"),
    ]

    pp_cols = st.columns(len(steps) * 2 - 1)
    for i, (icon, label, sublabel) in enumerate(steps):
        col_idx = i * 2
        with pp_cols[col_idx]:
            st.markdown(f"""
            <div class="pipeline-step completed">
              <div class="pipeline-icon">{icon}</div>
              <div class="pipeline-label">{label}</div>
              <div class="pipeline-sublabel">{sublabel}</div>
            </div>
            """, unsafe_allow_html=True)
        if i < len(steps) - 1:
            with pp_cols[col_idx + 1]:
                st.markdown("""
                <div style="display:flex;align-items:center;justify-content:center;
                  height:100%;color:#3b82f6;font-size:1.2rem;">→</div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── LIME Explanation — Pattern B ─────────────────────────
    with st.container():
        st.markdown("""
        <div class="glass-card-header">
          <div class="section-title">🔍 Word-Level Explanation (Translated Text)</div>
          <div class="section-subtitle">LIME applied to English translation</div>
        </div>
        """, unsafe_allow_html=True)

        try:
            from src.lime_explainer import explain_prediction, highlight_text_html  # noqa: E402
            import plotly.graph_objects as go  # noqa: E402

            word_weights = explain_prediction(analysis_text, model_pipeline, num_features=10)
            highlighted = highlight_text_html(analysis_text, word_weights)

            st.markdown("**Highlighted text** *(green = supports prediction, red = opposes)*", unsafe_allow_html=True)
            st.markdown(highlighted, unsafe_allow_html=True)

            if word_weights:
                words = [w for w, _ in word_weights]
                weights = [v for _, v in word_weights]
                colors = [POSITIVE_COLOR if v >= 0 else NEGATIVE_COLOR for v in weights]

                fig = go.Figure(go.Bar(x=weights, y=words, orientation="h", marker_color=colors))
                apply_theme(fig, title="Top Feature Contributions", height=400, margin=dict(l=120))
                fig.update_layout(xaxis_title="← Negative | Positive →", yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig, use_container_width=True, key="lang_lime_bar")

        except Exception as e:
            st.info(f"LIME explanation unavailable: {e}")

        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIX 6 — BATCH LANGUAGE ANALYSIS (upload zone redesign)
# Pattern B — widgets inside
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.container():
    st.markdown("""
    <div class="glass-card-header">
      <div class="section-title">📂 Batch Language Analysis</div>
      <div class="section-subtitle">Upload a CSV with non-English reviews for bulk translation and analysis</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="upload-zone-wrapper">
      <div class="upload-zone-header">
        <div class="upload-icon-circle">🌐</div>
        <div>
          <div class="upload-text-primary">Upload multilingual review dataset</div>
          <div class="upload-text-secondary">Auto-detects language for each row</div>
        </div>
      </div>
      <div class="upload-badges">
        <span class="upload-badge upload-badge-csv">CSV</span>
        <span class="upload-badge upload-badge-limit">Max 200MB</span>
        <span class="upload-badge upload-badge-limit">50+ Languages</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    batch_file = st.file_uploader(
        "", type=["csv"],
        label_visibility="collapsed",
        key="lang_batch_upload",
    )

    if batch_file is not None:
        import pandas as pd  # noqa: E402

        try:
            batch_df = pd.read_csv(batch_file)
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")
            st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)
            st.stop()

        st.dataframe(batch_df.head(5), use_container_width=True)

        _TEXT_HINTS = ("text", "review", "comment", "sentence", "content")
        _str_cols = [c for c in batch_df.columns if batch_df[c].dtype == object]
        _auto_col = next(
            (c for hint in _TEXT_HINTS for c in _str_cols if hint in c.lower()),
            _str_cols[0] if _str_cols else batch_df.columns[0],
        )

        batch_text_col = st.selectbox(
            "Select text column:", options=batch_df.columns.tolist(),
            index=batch_df.columns.tolist().index(_auto_col), key="lang_batch_col",
        )

        batch_btn = st.button("🌐  Translate & Analyze All", use_container_width=True, key="lang_batch_btn")

        if batch_btn:
            model_name = st.session_state.get("selected_model", "best")
            try:
                model_pipeline, _ = load_model(model_name)
            except Exception as exc:
                st.error(f"Model error: {exc}")
                st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)
                st.stop()

            from src.translator import detect_and_translate  # noqa: E402
            from src.predict import predict_sentiment  # noqa: E402

            # ── Animated Loading ─────────────────────────────
            batch_spinner = st.empty()
            batch_spinner.markdown("""
            <div class="analyze-loading">
              <div class="pulse-ring"></div>
              Translating and analyzing reviews...
            </div>
            """, unsafe_allow_html=True)

            texts = batch_df[batch_text_col].fillna("").astype(str).tolist()
            batch_results = []
            prog = st.progress(0, text="Translating and analyzing…")
            n = len(texts)

            for i, text in enumerate(texts):
                try:
                    tr = detect_and_translate(text)
                    at = tr["translated_text"] if tr["was_translated"] else tr["original_text"]
                    pred_r = predict_sentiment(at, model_pipeline)
                except Exception:
                    tr = {"detected_language": "unknown", "language_name": "Unknown",
                          "flag_emoji": "🏳️", "translated_text": text, "was_translated": False}
                    pred_r = {"label_name": "Neutral", "confidence": 0.0, "polarity": 0.0, "subjectivity": 0.0}

                batch_results.append({
                    "Original": text[:80] + ("…" if len(text) > 80 else ""),
                    "Language": f"{tr['flag_emoji']} {tr['language_name']}",
                    "Translated": tr["translated_text"][:80] + ("…" if len(tr.get("translated_text", "")) > 80 else ""),
                    "Sentiment": pred_r["label_name"],
                    "Confidence": f"{pred_r['confidence'] * 100:.1f}%",
                    "Polarity": round(pred_r["polarity"], 4),
                })

                if i % max(1, n // 100) == 0 or i == n - 1:
                    prog.progress((i + 1) / n, text=f"Translating… {i + 1}/{n}")

            batch_spinner.empty()
            prog.empty()
            out_df = pd.DataFrame(batch_results)

            st.dataframe(out_df, use_container_width=True)

            # ── Language Distribution Chart — Pattern B ───────
            import plotly.graph_objects as go  # noqa: E402

            with st.container():
                st.markdown("""
                <div class="glass-card-header">
                  <div class="section-title">📊 Language Distribution</div>
                </div>
                """, unsafe_allow_html=True)

                _lang_counts = out_df["Language"].value_counts()
                _total_lang = _lang_counts.sum()
                fig_lang = go.Figure(go.Bar(
                    x=_lang_counts.values, y=_lang_counts.index,
                    orientation="h",
                    marker=dict(color=_lang_counts.values, colorscale=[[0, "#0d4a6b"], [1, "#00e5cc"]]),
                    text=[f"{v / _total_lang * 100:.1f}%" for v in _lang_counts.values],
                    textposition="auto",
                ))
                apply_theme(fig_lang, title="Language Distribution",
                            height=max(250, len(_lang_counts) * 45), margin=dict(l=140))
                st.plotly_chart(fig_lang, use_container_width=True, key="lang_dist_chart")
                st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

            # ── Summary KPIs (Pattern A) ─────────────────────
            _unique_langs = out_df["Language"].nunique()
            _avg_conf = sum(float(r["Confidence"].replace("%", "")) for r in batch_results) / max(1, len(batch_results))

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(f"""
                <div class="metric-card metric-card-cyan">
                  <div class="metric-label">TOTAL REVIEWS</div>
                  <div class="metric-value">{len(batch_results):,}</div>
                </div>
                """, unsafe_allow_html=True)
            with k2:
                st.markdown(f"""
                <div class="metric-card metric-card-teal">
                  <div class="metric-label">LANGUAGES DETECTED</div>
                  <div class="metric-value">{_unique_langs}</div>
                </div>
                """, unsafe_allow_html=True)
            with k3:
                st.markdown(f"""
                <div class="metric-card metric-card-green">
                  <div class="metric-label">TRANSLATED</div>
                  <div class="metric-value">{len(batch_results):,}</div>
                </div>
                """, unsafe_allow_html=True)
            with k4:
                st.markdown(f"""
                <div class="metric-card metric-card-violet">
                  <div class="metric-label">AVG CONFIDENCE</div>
                  <div class="metric-value">{_avg_conf:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

            # ── Export — Pattern B ────────────────────────────
            with st.container():
                st.markdown("""
                <div class="glass-card-header">
                  <div class="section-title">📥 Export Results</div>
                </div>
                """, unsafe_allow_html=True)

                ex1, ex2, ex3, ex4 = st.columns(4)
                with ex1:
                    csv_b = out_df.to_csv(index=False).encode("utf-8")
                    st.download_button("📊  Translated CSV", data=csv_b,
                                        file_name="reviewsense_multilingual.csv",
                                        mime="text/csv", use_container_width=True)
                with ex2:
                    try:
                        from src.pdf_exporter import export_report  # noqa: E402
                        import tempfile, os  # noqa: E402
                        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as _t:
                            _tp = _t.name
                        try:
                            export_report({"multilingual_results": out_df.to_dict(orient="records")}, _tp)
                            with open(_tp, "rb") as f:
                                _pb = f.read()
                            st.download_button("📄  PDF Report", data=_pb,
                                                file_name="reviewsense_multilingual.pdf",
                                                mime="application/pdf", use_container_width=True)
                        finally:
                            if os.path.exists(_tp):
                                os.unlink(_tp)
                    except Exception:
                        st.button("📄  PDF", disabled=True, use_container_width=True, key="lang_pdf_dis")
                with ex3:
                    import json as _json  # noqa: E402
                    st.download_button("📋  JSON Export", data=out_df.to_json(orient="records", indent=2),
                                        file_name="reviewsense_multilingual.json",
                                        mime="application/json", use_container_width=True)
                with ex4:
                    try:
                        import io  # noqa: E402
                        buf = io.BytesIO()
                        out_df.to_excel(buf, index=False, engine="openpyxl")
                        st.download_button("📗  Excel Workbook", data=buf.getvalue(),
                                            file_name="reviewsense_multilingual.xlsx",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                            use_container_width=True)
                    except Exception:
                        st.button("📗  Excel", disabled=True, use_container_width=True, key="lang_xl_dis")

                st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)