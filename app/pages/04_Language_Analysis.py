"""Multilingual Sentiment Analysis — ReviewSense Analytics."""

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
    page_title="Language Analysis — ReviewSense",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── UI imports ───────────────────────────────────────────────
from ui.sidebar import load_css, render_sidebar            # noqa: E402
from ui.components import (                                 # noqa: E402
    page_header, section_title, glass_card, language_card,
    sentiment_badge, step_card, metric_card,
    sentiment_badge_html,
)
from ui.theme import (                                      # noqa: E402
    apply_theme, POSITIVE_COLOR, NEGATIVE_COLOR,
    NEUTRAL_COLOR, ACCENT_BLUE, ACCENT_PURPLE,
    ACCENT_CYAN, CHART_PALETTE,
)
from src.config import MODEL_NAMES                          # noqa: E402
from utils import load_model                            # noqa: E402

load_css()
render_sidebar()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

page_header(
    "🌐",
    "Multilingual Sentiment Analysis",
    "Detect language, translate to English, and run sentiment analysis — all in one step",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SUPPORTED LANGUAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

section_title("Supported Languages", icon="🗺️")

_LANGS = [
    ("🇬🇧", "English",  "EN"),
    ("🇮🇳", "Hindi",    "HI"),
    ("🇮🇳", "Tamil",    "TA"),
    ("🇮🇳", "Bengali",  "BN"),
    ("🇪🇸", "Spanish",  "ES"),
    ("🇫🇷", "French",   "FR"),
    ("🇩🇪", "German",   "DE"),
    ("🇨🇳", "Chinese",  "ZH-CN"),
]

_LANG_CODES = {"English": "en", "Hindi": "hi", "Tamil": "ta",
               "Bengali": "bn", "Spanish": "es", "French": "fr",
               "German": "de", "Chinese": "zh-cn"}

lang_cols = st.columns(len(_LANGS))
for col, (flag, name, code) in zip(lang_cols, _LANGS):
    with col:
        language_card(flag, name, code)

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANALYZE TEXT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

section_title("Analyze Text", icon="✏️")

# ── Page-level model selector ────────────────────────────────
_mc1, _mc2 = st.columns([3, 1])
with _mc2:
    model_name = st.selectbox("Model", ["best"] + MODEL_NAMES, index=0, key="lang_model")

lang_input_text = st.text_area(
    "Review Text (any language)",
    placeholder="La batterie dure longtemps, mais l'écran est trop sombre. Dans l'ensemble, c'est un bon produit.",
    height=120,
    key="lang_input",
)

st.markdown("<div class='gradient-btn'>", unsafe_allow_html=True)
analyze_btn = st.button("🌐  Detect & Analyze", use_container_width=True, key="lang_analyze")
st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DETECTION & ANALYSIS RESULT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if analyze_btn:
    if not lang_input_text.strip():
        st.warning("Please enter some text before analyzing.")
        st.stop()

    with st.spinner("Detecting language and translating…"):
        try:
            from src.translator import detect_and_translate  # noqa: E402
            translation_result = detect_and_translate(lang_input_text)
        except Exception as exc:
            st.error(f"Language detection / translation error: {exc}")
            st.stop()

    detected_lang = translation_result["detected_language"]
    lang_name     = translation_result["language_name"]
    flag          = translation_result["flag_emoji"]
    translated    = translation_result["translated_text"]
    was_translated = translation_result["was_translated"]

    st.markdown("---")
    section_title("Detection & Analysis Result", icon="🔍")

    # ── Language + Sentiment side by side ─────────────────────
    try:
        model_pipeline, _ = load_model(model_name)
    except FileNotFoundError:
        st.error("🚫 Model not found. Train first:\n\n```\npython src/train_classical.py\n```")
        st.stop()
    except Exception as exc:
        st.error(f"Model loading error: {exc}")
        st.stop()

    from src.predict import predict_sentiment  # noqa: E402

    analysis_text = translated if was_translated else lang_input_text
    pred = predict_sentiment(analysis_text, model_pipeline)

    label_name   = pred["label_name"]
    confidence   = pred["confidence"]
    polarity     = pred["polarity"]
    subjectivity = pred["subjectivity"]

    det1, det2 = st.columns(2)
    with det1:
        glass_card(
            f"<div style='color:#64748b;font-size:0.7rem;text-transform:uppercase;"
            f"letter-spacing:0.1em;font-weight:600;'>Detected Language</div>"
            f"<div style='display:flex;align-items:center;gap:0.6rem;margin-top:0.5rem;'>"
            f"<span style='font-size:2rem;'>{flag}</span>"
            f"<div>"
            f"<div style='font-size:1.3rem;font-weight:700;'>{lang_name}</div>"
            f"<div style='color:#94a3b8;font-size:0.8rem;'>{detected_lang.upper()}</div>"
            f"</div></div>"
        )
    with det2:
        glass_card(
            f"<div style='color:#64748b;font-size:0.7rem;text-transform:uppercase;"
            f"letter-spacing:0.1em;font-weight:600;'>Sentiment Analysis Result</div>"
            f"<div style='margin-top:0.6rem;'>{sentiment_badge_html(label_name)}</div>"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Metrics ──────────────────────────────────────────────
    rm1, rm2, rm3 = st.columns(3)
    rm1.metric("🎯 Confidence", f"{confidence * 100:.1f}%")
    rm2.metric("📈 Polarity", f"{polarity:.3f}")
    rm3.metric("💭 Subjectivity", f"{subjectivity:.3f}")
    st.progress(float(confidence), text=f"Model confidence: {confidence*100:.1f}%")

    # ── Original vs Translated ───────────────────────────────
    if was_translated:
        st.markdown("<br>", unsafe_allow_html=True)
        t1, t2 = st.columns(2)
        with t1:
            st.markdown("**Original Text**")
            glass_card(f"<p style='color:#94a3b8;line-height:1.7;'>{lang_input_text}</p>")
        with t2:
            st.markdown("**Translated to English**")
            glass_card(f"<p style='color:#e2e8f0;line-height:1.7;'>{translated}</p>")

    # ── Processing Pipeline Visualization ────────────────────
    st.markdown("---")
    section_title("Processing Pipeline", icon="⚙️")

    pp1, pp2, pp3, pp4, pp5 = st.columns(5)
    with pp1: step_card(1, "Input Text")
    with pp2: step_card(2, "Language Detection")
    with pp3: step_card(3, "Translation")
    with pp4: step_card(4, "Sentiment Analysis")
    with pp5: step_card(5, "Explanation")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BATCH LANGUAGE ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("---")
section_title("Batch Language Analysis", icon="📂")
st.markdown(
    "<p style='color:#94a3b8;font-size:0.9rem;'>"
    "Upload a CSV with non-English reviews. The app will detect language, translate, and analyze each row.</p>",
    unsafe_allow_html=True,
)

batch_file = st.file_uploader("Upload CSV (non-English reviews)", type=["csv"], key="lang_batch_upload")

if batch_file is not None:
    import pandas as pd  # noqa: E402

    try:
        batch_df = pd.read_csv(batch_file)
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}")
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

    st.markdown("<div class='gradient-btn'>", unsafe_allow_html=True)
    batch_btn = st.button("🌐  Translate & Analyze All", use_container_width=True, key="lang_batch_btn")
    st.markdown("</div>", unsafe_allow_html=True)

    if batch_btn:
        try:
            model_pipeline, _ = load_model(model_name)
        except Exception as exc:
            st.error(f"Model error: {exc}")
            st.stop()

        from src.translator import detect_and_translate  # noqa: E402
        from src.predict import predict_sentiment        # noqa: E402

        texts = batch_df[batch_text_col].fillna("").astype(str).tolist()
        batch_results = []
        prog = st.progress(0, text="Translating and analyzing…")
        n = len(texts)

        for i, text in enumerate(texts):
            try:
                tr = detect_and_translate(text)
                at = tr["translated_text"] if tr["was_translated"] else tr["original_text"]
                pred = predict_sentiment(at, model_pipeline)
            except Exception:
                tr = {"detected_language": "unknown", "language_name": "Unknown",
                      "flag_emoji": "🏳️", "translated_text": text, "was_translated": False}
                pred = {"label_name": "Neutral", "confidence": 0.0, "polarity": 0.0, "subjectivity": 0.0}

            batch_results.append({
                "Original": text[:80] + ("…" if len(text) > 80 else ""),
                "Language": f"{tr['flag_emoji']} {tr['language_name']}",
                "Translated": tr["translated_text"][:80] + ("…" if len(tr.get("translated_text","")) > 80 else ""),
                "Sentiment": pred["label_name"],
                "Confidence": f"{pred['confidence']*100:.1f}%",
                "Polarity": round(pred["polarity"], 4),
            })

            if i % max(1, n // 100) == 0 or i == n - 1:
                prog.progress((i + 1) / n, text=f"Translating… {i + 1}/{n}")

        prog.empty()
        out_df = pd.DataFrame(batch_results)

        # ── Results ──────────────────────────────────────────
        st.dataframe(out_df, use_container_width=True)

        # ── Language Distribution Chart ──────────────────────
        import plotly.graph_objects as go  # noqa: E402

        _lang_counts = out_df["Language"].value_counts()
        fig_lang = go.Figure(go.Bar(
            x=_lang_counts.values, y=_lang_counts.index,
            orientation="h", marker_color=CHART_PALETTE[:len(_lang_counts)],
        ))
        apply_theme(fig_lang, title="Language Distribution", height=max(250, len(_lang_counts) * 45),
                    margin=dict(l=140))
        st.plotly_chart(fig_lang, use_container_width=True)

        # ── Export ───────────────────────────────────────────
        section_title("Export Report", icon="📥")

        ex1, ex2, ex3, ex4 = st.columns(4)
        with ex1:
            csv_b = out_df.to_csv(index=False).encode("utf-8")
            st.download_button("📊  Translated CSV", data=csv_b,
                                file_name="reviewsense_multilingual.csv",
                                mime="text/csv", use_container_width=True)
        with ex2:
            import json as _json  # noqa: E402
            st.download_button("📋  JSON Export", data=out_df.to_json(orient="records", indent=2),
                                file_name="reviewsense_multilingual.json",
                                mime="application/json", use_container_width=True)
        with ex3:
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
        with ex4:
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