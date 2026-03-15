"""Model Performance Dashboard page for ReviewSense Analytics."""

import json
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
    page_title="Model Dashboard — ReviewSense",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
from app.utils import load_css, render_sidebar  # noqa: E402

load_css()

render_sidebar(show_model_selector=False)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("<h1>📊 Model Performance Dashboard</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#9e9eb8;'>Compare trained model accuracy, F1 scores, "
    "confusion matrices, and ROC-AUC curves across all classifiers.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ---------------------------------------------------------------------------
# Load model_results.json
# ---------------------------------------------------------------------------
_RESULTS_PATH = _PROJECT_ROOT / "reports" / "model_results.json"

if not _RESULTS_PATH.exists():
    st.warning(
        "⚠️ `reports/model_results.json` not found.\n\n"
        "**Quick demo** — generate sample artifacts in seconds:\n\n"
        "```\npython scripts/generate_demo_artifacts.py\n```\n\n"
        "**Production** — train on the full dataset:\n\n"
        "```\npython src/train_classical.py\n```\n\n"
        "Then re-open this page."
    )
    st.stop()

with open(_RESULTS_PATH, encoding="utf-8") as f:
    model_results: dict = json.load(f)

import numpy as np  # noqa: E402
import plotly.graph_objects as go  # noqa: E402

# ---------------------------------------------------------------------------
# Accuracy + F1 comparison chart
# ---------------------------------------------------------------------------
st.markdown("## 🏆 Accuracy & F1 Comparison")
try:
    from src.evaluate import plot_accuracy_comparison  # noqa: E402

    fig_acc = plot_accuracy_comparison(_RESULTS_PATH)
    st.plotly_chart(fig_acc, use_container_width=True)
except Exception as exc:
    st.error(f"Chart generation error: {exc}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Best model callout
# ---------------------------------------------------------------------------
_scored = {
    name: metrics
    for name, metrics in model_results.items()
    if isinstance(metrics, dict) and "accuracy" in metrics
}

if _scored:
    _best_name = max(_scored, key=lambda n: _scored[n].get("accuracy", 0))
    _best = _scored[_best_name]
    st.markdown("## 🥇 Best Model")
    bc1, bc2, bc3 = st.columns(3)
    bc1.metric("🤖 Model", _best_name)
    bc2.metric("🎯 Accuracy", f"{_best.get('accuracy', 0) * 100:.2f}%")
    bc3.metric(
        "📊 Macro F1",
        f"{_best.get('f1', 0) * 100:.2f}%",
    )
    if "training_time_sec" in _best:
        st.caption(f"Training time: {_best['training_time_sec']:.2f}s")

st.markdown("---")

# ---------------------------------------------------------------------------
# Confusion matrices
# ---------------------------------------------------------------------------
st.markdown("## 🔢 Confusion Matrices")

_models_with_cm = {
    name: metrics
    for name, metrics in model_results.items()
    if isinstance(metrics, dict) and "confusion_matrix" in metrics
}

if not _models_with_cm:
    st.info("No confusion matrix data found in model_results.json.")
else:
    _cm_tabs = st.tabs(list(_models_with_cm.keys()))
    from src.evaluate import plot_confusion_matrix  # noqa: E402
    from src.config import LABEL_MAP  # noqa: E402

    _labels = sorted(LABEL_MAP.keys())

    for tab, (model_name, metrics) in zip(_cm_tabs, _models_with_cm.items()):
        with tab:
            try:
                cm_array = np.asarray(metrics["confusion_matrix"])
                fig_cm = plot_confusion_matrix(cm_array, model_name, _labels)
                st.plotly_chart(fig_cm, use_container_width=True)
            except Exception as exc:
                st.error(f"Could not render confusion matrix: {exc}")

st.markdown("---")

# ---------------------------------------------------------------------------
# ROC-AUC section
# ---------------------------------------------------------------------------
st.markdown("## 📈 ROC-AUC Curves")

_models_with_roc = {
    name: metrics
    for name, metrics in model_results.items()
    if isinstance(metrics, dict) and "roc" in metrics
}

if not _models_with_roc:
    st.info(
        "No ROC data found in model_results.json. "
        "ROC curves require pre-computed FPR/TPR values to be stored during training."
    )
else:
    fig_roc = go.Figure()
    _colors = ["#3ba7ff", "#00c851", "#ffa500", "#ff4b4b", "#a56eff"]
    for idx, (model_name, metrics) in enumerate(_models_with_roc.items()):
        roc_data = metrics["roc"]
        fig_roc.add_trace(
            go.Scatter(
                x=roc_data.get("fpr", []),
                y=roc_data.get("tpr", []),
                mode="lines",
                name=f"{model_name} (AUC={roc_data.get('auc', 0):.3f})",
                line=dict(color=_colors[idx % len(_colors)], width=2.5),
            )
        )
    fig_roc.add_trace(
        go.Scatter(
            x=[0, 1], y=[0, 1],
            mode="lines", name="Chance",
            line=dict(color="#cccccc", dash="dash"),
        )
    )
    fig_roc.update_layout(
        template="plotly_dark",
        title="One-vs-Rest ROC Curves",
        xaxis_title="False Positive Rate",
        yaxis_title="True Positive Rate",
        yaxis=dict(range=[0, 1.05]),
        xaxis=dict(range=[0, 1]),
    )
    st.plotly_chart(fig_roc, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Global Feature Importance (TF-IDF + model coefs)
# ---------------------------------------------------------------------------
st.markdown("## 🔑 Global Feature Importance")

_MODELS_DIR = _PROJECT_ROOT / "models" / "classical"
_vec_path = _MODELS_DIR / "tfidf_vectorizer.pkl"
_model_path = _MODELS_DIR / "best_model.pkl"

if not (_vec_path.exists() and _model_path.exists()):
    st.info(
        "Feature importance requires trained model files in `models/classical/`. "
        "Train the models first."
    )
else:
    try:
        import joblib  # noqa: E402
        from sklearn.pipeline import Pipeline  # noqa: E402

        _artifact = joblib.load(_model_path)
        if isinstance(_artifact, Pipeline):
            _vectorizer = _artifact.named_steps.get("tfidf")
            _classifier = _artifact.named_steps.get("clf")
        else:
            _vectorizer = joblib.load(_vec_path)
            _classifier = _artifact

        _feature_names = np.asarray(_vectorizer.get_feature_names_out())

        _coef = None
        if hasattr(_classifier, "coef_"):
            _coef = np.asarray(_classifier.coef_)
        elif hasattr(_classifier, "feature_importances_"):
            _fi = np.asarray(_classifier.feature_importances_)
            _top_idx = _fi.argsort()[-20:][::-1]
            _fi_col1, _fi_col2 = st.columns(2)
            with _fi_col1:
                st.markdown("**Top 20 Important Features**")
                fig_fi = go.Figure(
                    go.Bar(
                        x=_fi[_top_idx],
                        y=_feature_names[_top_idx],
                        orientation="h",
                        marker_color="#3ba7ff",
                    )
                )
                fig_fi.update_layout(
                    template="plotly_dark",
                    height=500,
                    margin=dict(l=160),
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_fi, use_container_width=True)
            _coef = None

        if _coef is not None:
            # LinearSVC / LR: coef_ is (n_classes, n_features)
            # class order follows classifier.classes_
            _classes = getattr(_classifier, "classes_", [0, 1, 2])
            _label_map = {0: "Negative", 1: "Neutral", 2: "Positive"}
            _pos_idx = list(_classes).index(2) if 2 in list(_classes) else -1
            _neg_idx = list(_classes).index(0) if 0 in list(_classes) else 0

            _fi_col1, _fi_col2 = st.columns(2)

            with _fi_col1:
                st.markdown("**Top 20 Words → Positive**")
                if _coef.ndim > 1 and _pos_idx >= 0:
                    _pos_coefs = _coef[_pos_idx]
                else:
                    _pos_coefs = _coef.ravel()
                _top_pos = _pos_coefs.argsort()[-20:][::-1]
                fig_pos = go.Figure(
                    go.Bar(
                        x=_pos_coefs[_top_pos],
                        y=_feature_names[_top_pos],
                        orientation="h",
                        marker_color="#00c851",
                    )
                )
                fig_pos.update_layout(
                    template="plotly_dark", height=500,
                    margin=dict(l=160), yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_pos, use_container_width=True)

            with _fi_col2:
                st.markdown("**Top 20 Words → Negative**")
                if _coef.ndim > 1 and _neg_idx >= 0:
                    _neg_coefs = _coef[_neg_idx]
                else:
                    _neg_coefs = -_coef.ravel()
                _top_neg = _neg_coefs.argsort()[-20:][::-1]
                fig_neg = go.Figure(
                    go.Bar(
                        x=_neg_coefs[_top_neg],
                        y=_feature_names[_top_neg],
                        orientation="h",
                        marker_color="#ff4b4b",
                    )
                )
                fig_neg.update_layout(
                    template="plotly_dark", height=500,
                    margin=dict(l=160), yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_neg, use_container_width=True)

    except Exception as exc:
        st.info(f"Feature importance unavailable: {exc}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Sentiment Trend Over Time
# ---------------------------------------------------------------------------
st.markdown("## 📅 Sentiment Trend Over Time")

_DATA_PATH = _PROJECT_ROOT / "data" / "processed" / "reviewsense_dataset.csv"

if not _DATA_PATH.exists():
    st.info("Dataset not found. Run preprocessing to generate the dataset.")
else:
    try:
        import pandas as pd  # noqa: E402

        _trend_df = pd.read_csv(_DATA_PATH, nrows=50000)
        _time_candidates = [c for c in _trend_df.columns if any(
            k in c.lower() for k in ("time", "date", "timestamp", "created")
        )]
        if not _time_candidates:
            st.info("No timestamp column found in the dataset. Trend chart skipped.")
        else:
            _time_col = _time_candidates[0]
            _label_col = next(
                (c for c in _trend_df.columns if "label" in c.lower()), None
            )
            _text_col = next(
                (c for c in _trend_df.columns if "text" in c.lower() or "review" in c.lower()), None
            )
            if _label_col and _text_col:
                _plot_df = _trend_df[[_text_col, _label_col, _time_col]].rename(
                    columns={_text_col: "text", _label_col: "label", _time_col: "time"}
                )
                from src.evaluate import plot_sentiment_trend  # noqa: E402

                fig_trend = plot_sentiment_trend(_plot_df)
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("Could not identify text/label columns for trend analysis.")
    except Exception as exc:
        st.info(f"Trend chart unavailable: {exc}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Training Data Stats
# ---------------------------------------------------------------------------
st.markdown("## 📦 Training Data Statistics")

if not _DATA_PATH.exists():
    st.info("Dataset not found. Run preprocessing to generate the dataset.")
else:
    try:
        import pandas as pd  # noqa: E402
        from src.config import LABEL_MAP  # noqa: E402

        _stats_df = pd.read_csv(_DATA_PATH, nrows=100000)
        _ts_col1, _ts_col2 = st.columns(2)

        # Domain pie chart
        _domain_col = next(
            (c for c in _stats_df.columns if any(
                k in c.lower() for k in ("domain", "source", "category", "dataset")
            )), None
        )
        if _domain_col:
            _domain_counts = _stats_df[_domain_col].value_counts()
            fig_domain = go.Figure(
                go.Pie(
                    labels=_domain_counts.index.tolist(),
                    values=_domain_counts.values.tolist(),
                    hole=0.4,
                )
            )
            fig_domain.update_layout(
                template="plotly_dark",
                title="Reviews by Domain",
                height=350,
            )
            with _ts_col1:
                st.plotly_chart(fig_domain, use_container_width=True)

        # Label distribution bar chart
        _lbl_col = next(
            (c for c in _stats_df.columns if "label" in c.lower()), None
        )
        if _lbl_col:
            _lbl_counts = _stats_df[_lbl_col].value_counts().sort_index()
            _lbl_names = [LABEL_MAP.get(int(k), str(k)) for k in _lbl_counts.index]
            _lbl_colors = ["#ff4b4b", "#ffa500", "#00c851"]
            fig_lbl = go.Figure(
                go.Bar(
                    x=_lbl_names,
                    y=_lbl_counts.values,
                    marker_color=_lbl_colors[: len(_lbl_names)],
                )
            )
            fig_lbl.update_layout(
                template="plotly_dark",
                title="Label Distribution",
                xaxis_title="Sentiment",
                yaxis_title="Count",
                height=350,
            )
            with _ts_col2:
                st.plotly_chart(fig_lbl, use_container_width=True)

    except Exception as exc:
        st.info(f"Training data stats unavailable: {exc}")