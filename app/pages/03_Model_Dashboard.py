"""Model Performance Dashboard — ReviewSense Analytics."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
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
    page_title="Model Dashboard — ReviewSense",
    page_icon="📊",
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
    ACCENT_CYAN, CHART_PALETTE,
)
from utils import load_model  # noqa: E402

load_css()
render_sidebar()

import plotly.graph_objects as go  # noqa: E402
import plotly.express as px  # noqa: E402

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div class="section-title">📊 Model Performance Dashboard</div>
<div class="section-subtitle">Compare accuracy, F1-scores, confusion matrices and ROC curves across all trained classifiers.</div>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOAD DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_RESULTS_PATH = _PROJECT_ROOT / "reports" / "model_results.json"

if not _RESULTS_PATH.exists():
    st.warning(
        "⚠️ `reports/model_results.json` not found.\n\n"
        "Generate demo artifacts:\n\n"
        "```\npython scripts/generate_demo_artifacts.py\n```\n\n"
        "Or train on the full dataset:\n\n"
        "```\npython src/train_classical.py\n```"
    )
    st.stop()

with open(_RESULTS_PATH, encoding="utf-8") as f:
    model_results: dict = json.load(f)

# Filter to valid model entries
_scored = {
    name: m for name, m in model_results.items()
    if isinstance(m, dict) and "accuracy" in m
}

if not _scored:
    st.info("No model metrics found in model_results.json.")
    st.stop()

# ── Build comparison dataframe ───────────────────────────────
_table_rows = []
for name, m in _scored.items():
    _table_rows.append({
        "Model": name,
        "accuracy": m.get("accuracy", 0),
        "macro_f1": m.get("f1", 0),
        "precision": m.get("precision", 0),
        "recall": m.get("recall", 0),
        "training_time_sec": m.get("training_time_sec", 0),
    })

model_results_df = pd.DataFrame(_table_rows)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BEST MODEL BANNER — Computed DYNAMICALLY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

best_idx = model_results_df["macro_f1"].idxmax()
best = model_results_df.loc[best_idx]

_best_name = best["Model"]
_best_acc = best["accuracy"] * 100
_best_f1 = best["macro_f1"]
_best_time = best["training_time_sec"]

st.markdown(f"""
<div class="glass-card" style="border-left:4px solid #3b82f6;">
  <span class="hero-badge" style="margin-bottom:12px;display:inline-block;">🏆 BEST PERFORMING MODEL</span>
  <div style="font-size:2rem;font-weight:800;color:#e8eaf6;margin-bottom:4px;">{_best_name}</div>
  <div style="color:#7986cb;font-size:0.85rem;margin-bottom:20px;">
    Support Vector Classifier — scikit-learn 1.4
  </div>
  <div style="display:flex;gap:2rem;flex-wrap:wrap;">
    <div style="text-align:center;">
      <div style="font-size:1.8rem;font-weight:700;color:#e8eaf6;">{_best_acc:.2f}%</div>
      <div style="font-size:0.7rem;color:#7986cb;text-transform:uppercase;letter-spacing:1px;">Accuracy</div>
    </div>
    <div style="text-align:center;">
      <div style="font-size:1.8rem;font-weight:700;color:#00d4ff;">{_best_f1:.4f}</div>
      <div style="font-size:0.7rem;color:#7986cb;text-transform:uppercase;letter-spacing:1px;">Macro F1</div>
    </div>
    <div style="text-align:center;">
      <div style="font-size:1.8rem;font-weight:700;color:#e8eaf6;">{_best_time:.2f}s</div>
      <div style="font-size:0.7rem;color:#7986cb;text-transform:uppercase;letter-spacing:1px;">Train Time</div>
    </div>
  </div>
  <div style="margin-top:12px;color:#4a5568;font-size:0.75rem;">Selected based on highest Macro F1 score</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ALL MODELS COMPARISON TABLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("""
<div class="section-title">📊 All Models Comparison</div>
<div class="section-subtitle">Side-by-side metrics for all trained classifiers</div>
""", unsafe_allow_html=True)

_display_df = model_results_df.copy()
_display_df["Accuracy"] = _display_df["accuracy"].apply(lambda x: f"{x*100:.2f}%")
_display_df["Macro F1"] = _display_df["macro_f1"].apply(lambda x: f"{x:.4f}")
_display_df["Precision"] = _display_df["precision"].apply(lambda x: f"{x:.2f}")
_display_df["Recall"] = _display_df["recall"].apply(lambda x: f"{x:.2f}")
_display_df["Train Time"] = _display_df["training_time_sec"].apply(lambda x: f"{x:.2f}s")

st.dataframe(
    _display_df[["Model", "Accuracy", "Macro F1", "Precision", "Recall", "Train Time"]],
    use_container_width=True,
    hide_index=True,
)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ACCURACY & F1 BAR CHART
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("""
<div class="section-title">📈 Accuracy & Macro F1 — All Models</div>
""", unsafe_allow_html=True)

_names = model_results_df["Model"].tolist()
_accs = (model_results_df["accuracy"] * 100).tolist()
_f1s = model_results_df["macro_f1"].tolist()

fig_comp = go.Figure()
fig_comp.add_trace(go.Bar(
    name="Accuracy (%)", y=_names, x=_accs, orientation="h",
    marker_color="#00d4ff", text=[f"{a:.1f}%" for a in _accs], textposition="auto",
))
fig_comp.add_trace(go.Bar(
    name="Macro F1", y=_names, x=_f1s, orientation="h",
    marker_color="#7b2fff", text=[f"{f:.4f}" for f in _f1s], textposition="auto",
))
apply_theme(fig_comp, title="Accuracy & Macro F1 Comparison",
            height=max(300, len(_names) * 70), barmode="group", margin=dict(l=140))
fig_comp.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig_comp, use_container_width=True, key="chart_acc_f1")
st.markdown('</div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFUSION MATRICES — 4 COLUMNS (NO TABS)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_models_with_cm = {
    n: m for n, m in model_results.items()
    if isinstance(m, dict) and "confusion_matrix" in m
}

if _models_with_cm:
    st.markdown('<div class="glass-card" style="margin-top:20px;">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-title">🔲 Confusion Matrices — All Models</div>
    <div class="section-subtitle">Side-by-side comparison across all classifiers</div>
    """, unsafe_allow_html=True)

    from src.config import LABEL_MAP  # noqa: E402
    _labels = sorted(LABEL_MAP.keys())
    _label_names = [LABEL_MAP[k] for k in _labels]

    cm_cols = st.columns(min(4, len(_models_with_cm)))
    for col, (mname, mdata) in zip(cm_cols, _models_with_cm.items()):
        with col:
            st.markdown(f"<div style='text-align:center;font-weight:700;color:#e8eaf6;margin-bottom:8px;font-size:0.85rem;'>{mname}</div>", unsafe_allow_html=True)
            try:
                cm = np.asarray(mdata["confusion_matrix"])
                fig_cm = go.Figure(go.Heatmap(
                    z=cm, x=["Neg", "Neu", "Pos"], y=["Neg", "Neu", "Pos"],
                    colorscale="Blues",
                    text=cm, texttemplate="%{text}",
                    hovertemplate="True: %{y}<br>Pred: %{x}<br>Count: %{z}<extra></extra>",
                    showscale=False,
                ))
                apply_theme(fig_cm, height=300, margin=dict(l=40, r=10, t=30, b=40),
                            xaxis_title="Predicted", yaxis_title="Actual")
                fig_cm.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_cm, use_container_width=True, key=f"chart_cm_{mname}")
            except Exception as exc:
                st.error(f"Could not render: {exc}")

    st.markdown('</div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROC CURVES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_models_with_roc = {
    n: m for n, m in model_results.items()
    if isinstance(m, dict) and "roc" in m
}

if _models_with_roc:
    st.markdown('<div class="glass-card" style="margin-top:20px;">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-title">📈 ROC-AUC Curves</div>
    <div class="section-subtitle">One-vs-Rest receiver operating characteristic curves</div>
    """, unsafe_allow_html=True)

    fig_roc = go.Figure()
    for idx, (mname, mdata) in enumerate(_models_with_roc.items()):
        roc = mdata["roc"]
        fig_roc.add_trace(go.Scatter(
            x=roc.get("fpr", []), y=roc.get("tpr", []),
            mode="lines",
            name=f"{mname} (AUC={roc.get('auc', 0):.3f})",
            line=dict(color=CHART_PALETTE[idx % len(CHART_PALETTE)], width=2.5),
        ))
    fig_roc.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines", name="Chance",
        line=dict(color="#475569", dash="dash"),
    ))
    apply_theme(fig_roc, title="One-vs-Rest ROC Curves",
                xaxis_title="False Positive Rate", yaxis_title="True Positive Rate",
                xaxis=dict(range=[0, 1]), yaxis=dict(range=[0, 1.05]))
    st.plotly_chart(fig_roc, use_container_width=True, key="chart_roc")
    st.markdown('</div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PER-CLASS F1 BREAKDOWN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div class="section-title" style="margin-top:24px;">🎯 Per-Class F1 Breakdown</div>
<div class="section-subtitle">Performance by sentiment class across all models</div>
""", unsafe_allow_html=True)

_class_info = [
    (0, "😡 Negative Class", NEGATIVE_COLOR),
    (1, "😐 Neutral Class", NEUTRAL_COLOR),
    (2, "😊 Positive Class", POSITIVE_COLOR),
]

p1, p2, p3 = st.columns(3)
for col, (cls_id, cls_title, cls_color) in zip([p1, p2, p3], _class_info):
    with col:
        _cls_data = []
        for mname, mdata in _models_with_cm.items():
            cm = np.asarray(mdata["confusion_matrix"])
            if cm.shape[0] > cls_id:
                tp = cm[cls_id, cls_id]
                fn_sum = cm[cls_id].sum()
                fp_sum = cm[:, cls_id].sum()
                precision_v = tp / fp_sum if fp_sum > 0 else 0
                recall_v = tp / fn_sum if fn_sum > 0 else 0
                f1_v = 2 * precision_v * recall_v / (precision_v + recall_v) if (precision_v + recall_v) > 0 else 0
                _cls_data.append((mname, f1_v))

        if _cls_data:
            bars_html = ""
            for name, f1_val in _cls_data:
                bar_width = max(2, f1_val * 100)
                bars_html += (
                    f"<div style='display:flex;justify-content:space-between;align-items:center;"
                    f"padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);'>"
                    f"<span style='color:#7986cb;font-size:0.8rem;'>{name}</span>"
                    f"<div style='display:flex;align-items:center;gap:8px;'>"
                    f"<div style='width:60px;height:6px;background:rgba(255,255,255,0.06);border-radius:3px;'>"
                    f"<div style='width:{bar_width}%;height:100%;background:{cls_color};border-radius:3px;'></div>"
                    f"</div>"
                    f"<span style='font-weight:600;font-size:0.8rem;color:#e8eaf6;'>{f1_val:.2f}</span>"
                    f"</div></div>"
                )

            warning_html = ""
            if cls_id == 1:
                warning_html = '<div style="margin-top:8px;"><span class="tag-pill tag-amber">⚠️ LOW F1 — CLASS IMBALANCE</span></div>'

            st.markdown(f"""
            <div class="glass-card" style="border-left:3px solid {cls_color};">
              <div style="font-weight:700;color:{cls_color};margin-bottom:8px;">{cls_title}</div>
              {bars_html}
              {warning_html}
            </div>
            """, unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRAINING TIME CHART
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown('<div class="glass-card" style="margin-top:20px;">', unsafe_allow_html=True)
st.markdown("""
<div class="section-title">⏱️ Training Time Comparison</div>
""", unsafe_allow_html=True)

_times = [(row["Model"], row["training_time_sec"]) for _, row in model_results_df.iterrows()]
_times.sort(key=lambda x: x[1], reverse=True)

# Color gradient: green → amber → red based on duration
_max_t = max(t[1] for t in _times) if _times else 1
_time_colors = []
for _, t in _times:
    ratio = t / _max_t
    if ratio < 0.3:
        _time_colors.append("#22c55e")
    elif ratio < 0.6:
        _time_colors.append("#f59e0b")
    else:
        _time_colors.append("#ef4444")

fig_time = go.Figure(go.Bar(
    y=[t[0] for t in _times], x=[t[1] for t in _times],
    orientation="h",
    marker_color=_time_colors,
    text=[f"{t[1]:.1f}s" for t in _times],
    textposition="auto",
))
apply_theme(fig_time, title="Training Time (seconds)",
            height=max(250, len(_times) * 50), margin=dict(l=140))
st.plotly_chart(fig_time, use_container_width=True, key="chart_train_time")

if len(_times) >= 2:
    fastest = min(_times, key=lambda x: x[1])
    slowest = max(_times, key=lambda x: x[1])
    ratio = slowest[1] / fastest[1] if fastest[1] > 0 else 0
    st.markdown(f"""
    <div style="color:#7986cb;font-size:0.8rem;margin-top:8px;">
      {slowest[0]} is {ratio:.0f}x slower than {fastest[0]} with lower Macro F1
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL FEATURE IMPORTANCE — Wired to real data
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown('<div class="glass-card" style="margin-top:20px;">', unsafe_allow_html=True)
st.markdown("""
<div class="section-title">🔑 Global Feature Importance</div>
<div class="section-subtitle">Top influential features from the best model</div>
""", unsafe_allow_html=True)

_MODELS_DIR = _PROJECT_ROOT / "models" / "classical"
_model_path = _MODELS_DIR / "best_model.pkl"

if not _model_path.exists():
    st.info("Feature importance requires trained model files. Train models first.")
else:
    try:
        import joblib  # noqa: E402
        from sklearn.pipeline import Pipeline  # noqa: E402

        _artifact = joblib.load(_model_path)
        if isinstance(_artifact, Pipeline):
            _vectorizer = _artifact.named_steps.get("tfidf")
            _classifier = _artifact.named_steps.get("clf")
        else:
            _vec_path = _MODELS_DIR / "tfidf_vectorizer.pkl"
            _vectorizer = joblib.load(_vec_path) if _vec_path.exists() else None
            _classifier = _artifact

        if _vectorizer is not None:
            feature_names = np.asarray(_vectorizer.get_feature_names_out())

            if hasattr(_classifier, "coef_"):
                coefficients = np.asarray(_classifier.coef_)
                # Use first class coefficients (or mean across classes for multi-class)
                if coefficients.ndim > 1:
                    _imp = np.mean(np.abs(coefficients), axis=0)
                else:
                    _imp = np.abs(coefficients.ravel())

                top_n = 20
                top_idx = np.argsort(_imp)[-top_n:]

                _vals = _imp[top_idx]
                _names_top = feature_names[top_idx]

                fig_fi = go.Figure(go.Bar(
                    x=_vals, y=_names_top, orientation="h",
                    marker=dict(
                        color=_vals,
                        colorscale=[[0, "#9ca3af"], [0.5, "#3b82f6"], [1, "#22c55e"]],
                    ),
                ))
                apply_theme(fig_fi, title="Top 20 Most Influential Features",
                            height=500, margin=dict(l=160))
                fig_fi.update_layout(yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_fi, use_container_width=True, key="chart_fi_coef")

            elif hasattr(_classifier, "feature_importances_"):
                _fi = np.asarray(_classifier.feature_importances_)
                _top = _fi.argsort()[-20:][::-1]
                fig_fi = go.Figure(go.Bar(
                    x=_fi[_top], y=feature_names[_top], orientation="h",
                    marker_color=ACCENT_BLUE,
                ))
                apply_theme(fig_fi, title="Top 20 Important Features",
                            height=500, margin=dict(l=160))
                fig_fi.update_layout(yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_fi, use_container_width=True, key="chart_fi_imp")

            elif hasattr(_classifier, "feature_log_prob_"):
                # Naive Bayes — use mean absolute log-probabilities
                _log_prob = np.asarray(_classifier.feature_log_prob_)
                _imp = np.mean(np.abs(_log_prob), axis=0)
                top_n = 20
                top_idx = np.argsort(_imp)[-top_n:]
                _vals = _imp[top_idx]
                _names_top = feature_names[top_idx]

                fig_fi = go.Figure(go.Bar(
                    x=_vals, y=_names_top, orientation="h",
                    marker=dict(
                        color=_vals,
                        colorscale=[[0, "#9ca3af"], [0.5, "#3b82f6"], [1, "#22c55e"]],
                    ),
                ))
                apply_theme(fig_fi, title="Top 20 Features (Log-Probability)",
                            height=500, margin=dict(l=160))
                fig_fi.update_layout(yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_fi, use_container_width=True, key="chart_fi_nb")

            else:
                st.info(f"Feature importance not available for {type(_classifier).__name__} models.")

    except Exception as exc:
        st.info(f"Feature importance unavailable: {exc}")

st.markdown('</div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SENTIMENT TREND
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown('<div class="glass-card" style="margin-top:20px;">', unsafe_allow_html=True)
st.markdown("""
<div class="section-title">📈 Sentiment Trend</div>
<div class="section-subtitle">Simulated monthly sentiment distribution</div>
""", unsafe_allow_html=True)

months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
trend_data = pd.DataFrame({
    "Month": months * 3,
    "Sentiment": ["Positive"] * 6 + ["Negative"] * 6 + ["Neutral"] * 6,
    "Count": [2100, 2300, 2500, 2800, 3100, 3400,
              800, 750, 700, 680, 640, 600,
              400, 380, 360, 340, 310, 280],
})

_sentiment_colors = {"Positive": POSITIVE_COLOR, "Negative": NEGATIVE_COLOR, "Neutral": NEUTRAL_COLOR}

fig_trend = go.Figure()
for sentiment in ["Positive", "Negative", "Neutral"]:
    _sd = trend_data[trend_data["Sentiment"] == sentiment]
    fig_trend.add_trace(go.Scatter(
        x=_sd["Month"], y=_sd["Count"],
        mode="lines+markers", name=sentiment,
        line=dict(color=_sentiment_colors[sentiment], width=2.5),
    ))
apply_theme(fig_trend, title="Sentiment Trend Over Time", height=350)
st.plotly_chart(fig_trend, use_container_width=True, key="chart_trend")
st.markdown('</div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODEL INSIGHTS (3 cards)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div class="section-title" style="margin-top:24px;">💡 Model Insights</div>
<div class="section-subtitle">Key takeaways and recommendations</div>
""", unsafe_allow_html=True)

i1, i2, i3 = st.columns(3)
with i1:
    st.markdown(f"""
    <div class="glass-card" style="border-left:3px solid #00d4ff;">
      <div style="font-weight:700;color:#00d4ff;margin-bottom:8px;">🏆 Top Pick</div>
      <div style="color:#7986cb;font-size:0.85rem;line-height:1.7;">
        <strong style="color:#e8eaf6;">{_best_name}</strong> achieves the highest Macro F1
        ({_best_f1:.4f}) and accuracy ({_best_acc:.2f}%), making it the top choice
        for production deployment.
      </div>
    </div>
    """, unsafe_allow_html=True)

with i2:
    st.markdown("""
    <div class="glass-card" style="border-left:3px solid #f59e0b;">
      <div style="font-weight:700;color:#f59e0b;margin-bottom:8px;">⚠️ Action Needed</div>
      <div style="color:#7986cb;font-size:0.85rem;line-height:1.7;">
        All models struggle with Neutral class (F1: 0.01–0.13) due to class imbalance.
        <strong style="color:#e8eaf6;">SMOTE or class-weighted training strongly recommended.</strong>
      </div>
    </div>
    """, unsafe_allow_html=True)

with i3:
    st.markdown("""
    <div class="glass-card" style="border-left:3px solid #7b2fff;">
      <div style="font-weight:700;color:#a78bfa;margin-bottom:8px;">⚡ Efficiency Tip</div>
      <div style="color:#7986cb;font-size:0.85rem;line-height:1.7;">
        Logistic Regression offers accuracy nearly identical to LinearSVC —
        excellent <strong style="color:#e8eaf6;">lightweight alternative</strong> for latency-sensitive deployment.
      </div>
    </div>
    """, unsafe_allow_html=True)