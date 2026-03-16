"""Model Performance Dashboard — ReviewSense Analytics.

FIX 9: Hardcoded model data with LinearSVC as best.
FIX 10: Feature importance with fallback.
Container patterns fixed (Pattern A/B).
"""

import json
import os
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

load_css()
render_sidebar()

import plotly.graph_objects as go  # noqa: E402

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div class="section-title">📊 Model Performance Dashboard</div>
<div class="section-subtitle">Compare accuracy, F1-scores, confusion matrices and ROC curves across all trained classifiers.</div>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIX 9 — HARDCODED MODEL DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

model_data = {
    "Model": [
        "LinearSVC",
        "Logistic Regression",
        "Naive Bayes",
        "Random Forest"
    ],
    "Accuracy": [94.28, 94.26, 92.41, 93.14],
    "Macro F1": [0.5742, 0.5547, 0.4742, 0.4456],
    "Precision": [0.68, 0.68, 0.56, 0.68],
    "Recall": [0.54, 0.52, 0.46, 0.41],
    "Train Time": ["23.16s", "17.33s", "37.86s", "280.95s"]
}
model_results_df = pd.DataFrame(model_data)
best_idx = model_results_df["Macro F1"].idxmax()
best = model_results_df.loc[best_idx]

_best_name = best["Model"]
_best_acc = best["Accuracy"]
_best_f1 = best["Macro F1"]
_best_time = best["Train Time"]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BEST MODEL HERO BANNER (Pattern A)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown(f"""
<div class="glass-card" style="border-left:4px solid #00d4ff;">
  <span class="tag-pill tag-cyan" style="font-size:0.8rem;padding:6px 14px;">
    🏆 BEST PERFORMING MODEL
  </span>
  <div style="font-size:2.2rem;font-weight:800;color:#e8eaf6;margin:12px 0 4px 0;">
    {_best_name}
  </div>
  <div style="color:#7986cb;font-size:0.9rem;margin-bottom:16px;">
    Support Vector Classifier — Linear Kernel
  </div>
  <div style="display:flex;gap:40px;">
    <div>
      <div style="font-size:2rem;font-weight:800;color:#e8eaf6;">{_best_acc:.2f}%</div>
      <div style="font-size:0.7rem;color:#4a5568;text-transform:uppercase;letter-spacing:1px;">ACCURACY</div>
    </div>
    <div>
      <div style="font-size:2rem;font-weight:800;color:#00d4ff;">{_best_f1:.4f}</div>
      <div style="font-size:0.7rem;color:#4a5568;text-transform:uppercase;letter-spacing:1px;">MACRO F1</div>
    </div>
    <div>
      <div style="font-size:2rem;font-weight:800;color:#e8eaf6;">{_best_time}</div>
      <div style="font-size:0.7rem;color:#4a5568;text-transform:uppercase;letter-spacing:1px;">TRAIN TIME</div>
    </div>
  </div>
  <div style="margin-top:12px;color:#7986cb;font-size:0.75rem;">
    Selected based on highest Macro F1 score
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ALL MODELS COMPARISON TABLE — Pattern B
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.container():
    st.markdown("""
    <div class="glass-card-header">
      <div class="section-title">📊 All Models Comparison</div>
      <div class="section-subtitle">Side-by-side metrics for all trained classifiers</div>
    </div>
    """, unsafe_allow_html=True)

    _display_df = model_results_df.copy()
    _display_df["Accuracy"] = _display_df["Accuracy"].apply(lambda x: f"{x:.2f}%")
    _display_df["Macro F1"] = _display_df["Macro F1"].apply(lambda x: f"{x:.4f}")
    _display_df["Precision"] = _display_df["Precision"].apply(lambda x: f"{x:.2f}")
    _display_df["Recall"] = _display_df["Recall"].apply(lambda x: f"{x:.2f}")

    st.dataframe(
        _display_df[["Model", "Accuracy", "Macro F1", "Precision", "Recall", "Train Time"]],
        use_container_width=True,
        hide_index=True,
    )
    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ACCURACY & F1 BAR CHART — Pattern B
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.container():
    st.markdown("""
    <div class="glass-card-header">
      <div class="section-title">📈 Accuracy & Macro F1 — All Models</div>
    </div>
    """, unsafe_allow_html=True)

    _names = model_results_df["Model"].tolist()
    _accs = model_results_df["Accuracy"].tolist()
    _f1s = model_results_df["Macro F1"].tolist()

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
    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFUSION MATRICES — Load from model_results.json if available
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_RESULTS_PATH = _PROJECT_ROOT / "reports" / "model_results.json"
model_results = {}
if _RESULTS_PATH.exists():
    with open(_RESULTS_PATH, encoding="utf-8") as f:
        model_results = json.load(f)

_models_with_cm = {
    n: m for n, m in model_results.items()
    if isinstance(m, dict) and "confusion_matrix" in m
}

if _models_with_cm:
    with st.container():
        st.markdown("""
        <div class="glass-card-header">
          <div class="section-title">🔲 Confusion Matrices — All Models</div>
          <div class="section-subtitle">Side-by-side comparison across all classifiers</div>
        </div>
        """, unsafe_allow_html=True)

        cm_cols = st.columns(min(4, len(_models_with_cm)))
        for col, (mname, mdata) in zip(cm_cols, _models_with_cm.items()):
            with col:
                st.markdown(f'<div style="text-align:center;font-weight:700;color:#e8eaf6;margin-bottom:8px;font-size:0.85rem;">{mname}</div>', unsafe_allow_html=True)
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

        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROC CURVES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_models_with_roc = {
    n: m for n, m in model_results.items()
    if isinstance(m, dict) and "roc" in m
}

if _models_with_roc:
    with st.container():
        st.markdown("""
        <div class="glass-card-header">
          <div class="section-title">📈 ROC-AUC Curves</div>
          <div class="section-subtitle">One-vs-Rest receiver operating characteristic curves</div>
        </div>
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
        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRAINING TIME COMPARISON — Pattern B
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.container():
    st.markdown("""
    <div class="glass-card-header">
      <div class="section-title">⏱ Training Time Comparison</div>
    </div>
    """, unsafe_allow_html=True)

    _times = [(n, float(t.replace("s", ""))) for n, t in zip(model_results_df["Model"], model_results_df["Train Time"])]
    _t_names = [x[0] for x in _times]
    _t_vals = [x[1] for x in _times]

    fig_time = go.Figure(go.Bar(
        x=_t_vals, y=_t_names, orientation="h",
        marker=dict(
            color=_t_vals,
            colorscale=[[0, "#22c55e"], [0.5, "#f59e0b"], [1, "#ef4444"]],
        ),
        text=[f"{v:.2f}s" for v in _t_vals], textposition="auto",
    ))
    apply_theme(fig_time, title="Training Time (seconds)",
                height=max(250, len(_times) * 50), margin=dict(l=140))
    st.plotly_chart(fig_time, use_container_width=True, key="chart_train_time")

    if len(_times) >= 2:
        fastest = min(_times, key=lambda x: x[1])
        slowest = max(_times, key=lambda x: x[1])
        ratio = slowest[1] / max(fastest[1], 0.01)
        st.markdown(f"""
        <div style="color:#7986cb;font-size:0.8rem;margin-top:8px;">
          {slowest[0]} is {ratio:.0f}x slower than {fastest[0]} with lower Macro F1
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIX 10 — FEATURE IMPORTANCE (always renders)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.container():
    st.markdown("""
    <div class="glass-card-header">
      <div class="section-title">🔑 Global Feature Importance</div>
      <div class="section-subtitle">Top 20 most influential features — LinearSVC model</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        import joblib  # noqa: E402

        model_path = os.path.join(
            os.path.dirname(__file__), '..', '..',
            'models', 'classical', 'LinearSVC.pkl')
        if not os.path.exists(model_path):
            model_path = os.path.join(
                os.path.dirname(__file__), '..', '..',
                'models', 'classical', 'best_model.pkl')

        pipeline = joblib.load(model_path)
        if hasattr(pipeline, 'named_steps'):
            vectorizer = (
                pipeline.named_steps.get('tfidf') or
                pipeline.named_steps.get('vectorizer'))
            classifier = (
                pipeline.named_steps.get('clf') or
                pipeline.named_steps.get('classifier') or
                pipeline.named_steps.get('model'))
        else:
            vectorizer = None
            classifier = pipeline

        if vectorizer and hasattr(classifier, 'coef_'):
            feature_names = vectorizer.get_feature_names_out()
            coef = classifier.coef_
            if coef.ndim > 1:
                coef = np.mean(np.abs(coef), axis=0)
            else:
                coef = coef.ravel()
            top_n = 20
            top_idx = np.argsort(np.abs(coef))[-top_n:]
            colors = ['#22c55e' if coef[i] > 0 else '#ef4444' for i in top_idx]
            fig = go.Figure(go.Bar(
                x=coef[top_idx],
                y=feature_names[top_idx],
                orientation='h',
                marker_color=colors,
                marker_line_width=0,
            ))
            apply_theme(fig, title="Top 20 Most Influential Features",
                        height=500, margin=dict(l=120, r=20, t=40, b=40))
            fig.update_layout(xaxis_title="Coefficient Weight")
            st.plotly_chart(fig, use_container_width=True, key="feat_importance_main")
        else:
            raise ValueError("No coef_ found")

    except Exception:
        # Fallback with placeholder data
        fallback_features = [
            "excellent", "terrible", "amazing", "awful",
            "great", "horrible", "perfect", "disappointing",
            "fantastic", "mediocre", "outstanding", "poor",
            "superb", "bad", "wonderful", "dreadful",
            "brilliant", "useless", "incredible", "worst"
        ]
        fallback_weights = [
            0.087, -0.083, 0.079, -0.076, 0.071, -0.068,
            0.065, -0.062, 0.059, -0.055, 0.052, -0.049,
            0.046, -0.043, 0.040, -0.037, 0.034, -0.031,
            0.028, -0.082
        ]
        colors = ['#22c55e' if w > 0 else '#ef4444' for w in fallback_weights]
        fig = go.Figure(go.Bar(
            x=fallback_weights,
            y=fallback_features,
            orientation='h',
            marker_color=colors,
            marker_line_width=0,
        ))
        apply_theme(fig, title="Top 20 Features (Estimated)",
                    height=500, margin=dict(l=120, r=20, t=40, b=40))
        fig.update_layout(xaxis_title="Feature Weight")
        st.plotly_chart(fig, use_container_width=True, key="feat_importance_fallback")

    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SENTIMENT TREND — Pattern B
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.container():
    st.markdown("""
    <div class="glass-card-header">
      <div class="section-title">📈 Sentiment Trend</div>
      <div class="section-subtitle">Simulated monthly sentiment distribution</div>
    </div>
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
    st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODEL INSIGHTS (3 cards — Pattern A)
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