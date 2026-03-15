"""Multilingual Sentiment Analysis page for ReviewSense Analytics."""

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
    page_title="Language Analysis — ReviewSense",
    layout="wide",
    page_icon="🌐",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
from utils import load_css, load_model, render_sidebar, sentiment_badge_html  # noqa: E402

load_css()

sidebar_opts = render_sidebar()

# ---------------------------------------------------------------------------
# Model loading (cached)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("<h1>🌐 Multilingual Sentiment Analysis</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#9e9eb8;'>Detect language, translate to English, and run "
    "sentiment analysis — all in one step.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ---------------------------------------------------------------------------
# Supported languages
# ---------------------------------------------------------------------------
st.markdown("## 🗺️ Supported Languages")

_LANG_CARDS = [
    ("🇬🇧", "English", "en"),
    ("🇮🇳", "Hindi", "hi"),
    ("🇮🇳", "Tamil", "ta"),
    ("🇮🇳", "Bengali", "bn"),
    ("🇪🇸", "Spanish", "es"),
    ("🇫🇷", "French", "fr"),
    ("🇩🇪", "German", "de"),
    ("🇨🇳", "Chinese", "zh-cn"),
]

lang_cols = st.columns(len(_LANG_CARDS))
for col, (flag, name, code) in zip(lang_cols, _LANG_CARDS):
    col.markdown(
        f"<div class='rs-card' style='text-align:center;padding:0.75rem;'>"
        f"<div style='font-size:2rem;'>{flag}</div>"
        f"<div style='font-weight:600;'>{name}</div>"
        f"<div style='color:#9e9eb8;font-size:0.75rem;'>{code}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Single text analysis
# ---------------------------------------------------------------------------
st.markdown("## 🔤 Analyze Text")

lang_input_text = st.text_area(
    "Enter review text (any language):",
    placeholder="e.g. La batterie dure longtemps mais l'écran est trop sombre.",
    height=120,
    key="lang_input",
)

analyze_lang_btn = st.button(
    "🌐 Detect & Analyze",
    use_container_width=True,
    key="lang_analyze_btn",
)

if analyze_lang_btn:
    if not lang_input_text.strip():
        st.warning("Please enter some text before analyzing.")
    else:
        with st.spinner("Detecting language and translating…"):
            try:
                from src.translator import detect_and_translate  # noqa: E402

                translation_result = detect_and_translate(lang_input_text)
            except Exception as exc:
                st.error(f"Language detection / translation error: {exc}")
                st.stop()

        # Language detection result
        detected_lang = translation_result["detected_language"]
        lang_name = translation_result["language_name"]
        flag = translation_result["flag_emoji"]
        translated = translation_result["translated_text"]
        was_translated = translation_result["was_translated"]

        st.markdown("### 🔍 Detected Language")
        st.markdown(
            f"<div class='rs-card'>"
            f"<span style='font-size:2rem;'>{flag}</span> "
            f"<b style='font-size:1.2rem;'>{lang_name}</b> "
            f"<code style='color:#9e9eb8;'>({detected_lang})</code>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Original vs translated side by side
        if was_translated:
            st.markdown("<br>", unsafe_allow_html=True)
            ot_col1, ot_col2 = st.columns(2)
            with ot_col1:
                st.markdown("**Original Text**")
                st.markdown(
                    f"<div class='rs-card'><p style='color:#9e9eb8;'>"
                    f"{lang_input_text}</p></div>",
                    unsafe_allow_html=True,
                )
            with ot_col2:
                st.markdown("**Translated to English**")
                st.markdown(
                    f"<div class='rs-card'><p style='color:#e8eaf6;'>"
                    f"{translated}</p></div>",
                    unsafe_allow_html=True,
                )

        # Sentiment prediction on translated text
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📊 Sentiment Result")

        analysis_text = translated if was_translated else lang_input_text

        try:
            model_pipeline, _ = load_model(sidebar_opts["model"])
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

        pred = predict_sentiment(analysis_text, model_pipeline)
        label_name = pred["label_name"]
        confidence = pred["confidence"]
        polarity = pred["polarity"]
        subjectivity = pred["subjectivity"]

        with st.container():
            badge_col, _ = st.columns([2, 5])
            with badge_col:
                st.markdown(sentiment_badge_html(label_name), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            rm1, rm2, rm3 = st.columns(3)
            rm1.metric("🎯 Confidence", f"{confidence * 100:.1f}%")
            rm2.metric("📈 Polarity", f"{polarity:.3f}")
            rm3.metric("💭 Subjectivity", f"{subjectivity:.3f}")
            st.progress(float(confidence), text=f"Model confidence: {confidence * 100:.1f}%")

st.markdown("---")

# ---------------------------------------------------------------------------
# Batch language analysis
# ---------------------------------------------------------------------------
st.markdown("## 📂 Batch Language Analysis")
st.markdown(
    "<p style='color:#9e9eb8;'>Upload a CSV with non-English reviews. "
    "The app will detect language, translate, and analyze each row.</p>",
    unsafe_allow_html=True,
)

batch_file = st.file_uploader(
    "📤 Upload CSV (non-English reviews)",
    type=["csv"],
    key="lang_batch_upload",
)

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
        "🔤 Select text column:",
        options=batch_df.columns.tolist(),
        index=batch_df.columns.tolist().index(_auto_col),
        key="lang_batch_text_col",
    )

    if st.button("🌐 Translate & Analyze All", use_container_width=True, key="lang_batch_btn"):
        try:
            model_pipeline, _ = load_model(sidebar_opts["model"])
        except FileNotFoundError:
            st.error(
                "🚫 Model file not found. Train the model first:\n\n"
                "```\npython src/train_classical.py\n```"
            )
            st.stop()
        except Exception as exc:
            st.error(f"Model loading error: {exc}")
            st.stop()

        from src.translator import detect_and_translate  # noqa: E402
        from src.predict import predict_sentiment  # noqa: E402

        texts = batch_df[batch_text_col].fillna("").astype(str).tolist()
        batch_results = []
        prog = st.progress(0, text="Translating and analyzing…")
        n = len(texts)

        for i, text in enumerate(texts):
            try:
                tr = detect_and_translate(text)
                analysis_text = tr["translated_text"] if tr["was_translated"] else tr["original_text"]
                pred = predict_sentiment(analysis_text, model_pipeline)
            except Exception:
                tr = {
                    "detected_language": "unknown",
                    "language_name": "Unknown",
                    "flag_emoji": "🏳️",
                    "translated_text": text,
                    "was_translated": False,
                }
                pred = {"label_name": "Neutral", "confidence": 0.0, "polarity": 0.0, "subjectivity": 0.0}

            batch_results.append({
                "Original": text[:80] + ("…" if len(text) > 80 else ""),
                "Language": f"{tr['flag_emoji']} {tr['language_name']}",
                "Translated": tr["translated_text"][:80] + ("…" if len(tr.get("translated_text", "")) > 80 else ""),
                "Sentiment": pred["label_name"],
                "Confidence": f"{pred['confidence'] * 100:.1f}%",
                "Polarity": round(pred["polarity"], 4),
            })

            if i % max(1, n // 100) == 0 or i == n - 1:
                prog.progress((i + 1) / n, text=f"Translating… {i + 1}/{n}")

        prog.empty()

        out_df = pd.DataFrame(batch_results)
        st.dataframe(out_df, use_container_width=True)

        csv_bytes = out_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Results CSV",
            data=csv_bytes,
            file_name="reviewsense_multilingual_results.csv",
            mime="text/csv",
            use_container_width=True,
        )