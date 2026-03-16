"""Model Performance Dashboard — ReviewSense Analytics."""

import json
import sys
from pathlib import Path

import numpy as np
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

# ── UI imports ───────────────────────────────────────────────
from ui.sidebar import load_css, render_sidebar            # noqa: E402
from ui.components import (                                 # noqa: E402
    page_header, section_title, glass_card, metric_card,
    hero_card, accent_badge,
)
from ui.theme import (                                      # noqa: E402
    apply_theme, POSITIVE_COLOR, NEGATIVE_COLOR,
    NEUTRAL_COLOR, ACCENT_BLUE, ACCENT_PURPLE,
    ACCENT_CYAN, CHART_PALETTE,
)

load_css()
render_sidebar()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

page_header(
    "📊",
    "Model Performance Dashboard",
    "Compare accuracy, F1-scores, confusion matrices and ROC curves across all trained classifiers",
)

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

import plotly.graph_objects as go  # noqa: E402

# Filter to valid model entries
_scored = {
    name: m for name, m in model_results.items()
    if isinstance(m, dict) and "accuracy" in m
}

if not _scored:
    st.info("No model metrics found in model_results.json.")
    st.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BEST MODEL HIGHLIGHT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_best_name = max(_scored, key=lambda n: _scored[n].get("f1", 0))
_best = _scored[_best_name]
_best_acc = _best.get("accuracy", 0) * 100
_best_f1  = _best.get("f1", 0)
_best_time = _best.get("training_time_sec", 0)

hero_card(
    f"""
    <span class='accent-badge' style='margin-bottom:0.75rem;display:inline-block;'>🏆 BEST PERFORMING MODEL</span>
    <div style='font-size:1.8rem;font-weight:700;color:#f1f5f9;margin-bottom:0.3rem;'>{_best_name}</div>
    <div style='color:#94a3b8;font-size:0.85rem;margin-bottom:1rem;'>
        Selected based on highest Macro F1 score across Negative, Neutral, and Positive classes on the test split.
    </div>
    <div style='display:flex;gap:1.5rem;flex-wrap:wrap;'>
        <div style='text-align:center;'>
            <div style='font-size:1.6rem;font-weight:700;color:#f1f5f9;'>{_best_acc:.2f}%</div>
            <div style='font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;'>Accuracy</div>
        </div>
        <div style='text-align:center;'>
            <div style='font-size:1.6rem;font-weight:700;color:{ACCENT_CYAN};'>{_best_f1:.4f}</div>
            <div style='font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;'>Macro F1</div>
        </div>
        <div style='text-align:center;'>
            <div style='font-size:1.6rem;font-weight:700;color:#f1f5f9;'>{_best_time:.2f}s</div>
            <div style='font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;'>Train Time</div>
        </div>
    </div>
    """
)

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ALL MODELS COMPARISON TABLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

section_title("All Models Comparison", icon="📋")

import pandas as pd  # noqa: E402

_table_rows = []
for name, m in _scored.items():
    _table_rows.append({
        "Model": name,
        "Accuracy": f"{m.get('accuracy', 0)*100:.2f}%",
        "Macro F1": f"{m.get('f1', 0):.4f}",
        "Precision": f"{m.get('precision', 0):.4f}",
        "Recall": f"{m.get('recall', 0):.4f}",
        "Train Time": f"{m.get('training_time_sec', 0):.2f}s",
    })

_table_df = pd.DataFrame(_table_rows)
st.dataframe(_table_df, use_container_width=True, hide_index=True)

st.markdown("<br>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ACCURACY & F1 BAR CHART
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

section_title("Accuracy & Macro F1 — All Models", icon="📊")

_names = list(_scored.keys())
_accs  = [_scored[n].get("accuracy", 0) * 100 for n in _names]
_f1s   = [_scored[n].get("f1", 0) for n in _names]

fig_comp = go.Figure()
fig_comp.add_trace(go.Bar(name="Accuracy (%)", y=_names, x=_accs, orientation="h",
                          marker_color=ACCENT_BLUE, text=[f"{a:.1f}%" for a in _accs], textposition="auto"))
fig_comp.add_trace(go.Bar(name="Macro F1", y=_names, x=_f1s, orientation="h",
                          marker_color=ACCENT_PURPLE, text=[f"{f:.4f}" for f in _f1s], textposition="auto"))
apply_theme(fig_comp, title="Accuracy & Macro F1 Comparison", height=max(300, len(_names) * 70),
            barmode="group", margin=dict(l=140))
fig_comp.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig_comp, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFUSION MATRICES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_models_with_cm = {
    n: m for n, m in model_results.items()
    if isinstance(m, dict) and "confusion_matrix" in m
}

if _models_with_cm:
    st.markdown("---")
    section_title("Confusion Matrices", icon="🔢")

    from src.config import LABEL_MAP  # noqa: E402
    _labels = sorted(LABEL_MAP.keys())
    _label_names = [LABEL_MAP[k] for k in _labels]

    _cm_tabs = st.tabs(list(_models_with_cm.keys()))
    for tab, (mname, mdata) in zip(_cm_tabs, _models_with_cm.items()):
        with tab:
            try:
                cm = np.asarray(mdata["confusion_matrix"])
                fig_cm = go.Figure(go.Heatmap(
                    z=cm, x=_label_names, y=_label_names,
                    colorscale=[[0, "rgba(7,11,20,1)"], [1, ACCENT_BLUE]],
                    text=cm, texttemplate="%{text}",
                    hovertemplate="True: %{y}<br>Pred: %{x}<br>Count: %{z}<extra></extra>",
                ))
                apply_theme(fig_cm, title=f"Confusion Matrix — {mname}", height=420,
                            xaxis_title="Predicted", yaxis_title="Actual",
                            margin=dict(l=80, t=60))
                fig_cm.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_cm, use_container_width=True)
            except Exception as exc:
                st.error(f"Could not render confusion matrix: {exc}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROC CURVES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_models_with_roc = {
    n: m for n, m in model_results.items()
    if isinstance(m, dict) and "roc" in m
}

if _models_with_roc:
    st.markdown("---")
    section_title("ROC-AUC Curves", icon="📈")

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
    st.plotly_chart(fig_roc, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PER-CLASS F1 BREAKDOWN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("---")
section_title("Per-Class Analysis", icon="🎯")

_class_colors = {0: NEGATIVE_COLOR, 1: NEUTRAL_COLOR, 2: POSITIVE_COLOR}
_class_names  = {0: "Negative", 1: "Neutral", 2: "Positive"}

p1, p2, p3 = st.columns(3)
for col, cls_id in zip([p1, p2, p3], [0, 1, 2]):
    with col:
        # compute per-class precision from confusion matrices
        _cls_data = []
        for mname, mdata in _models_with_cm.items():
            cm = np.asarray(mdata["confusion_matrix"])
            if cm.shape[0] > cls_id:
                tp = cm[cls_id, cls_id]
                fn = cm[cls_id].sum() - tp
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                _cls_data.append((mname, recall))

        if _cls_data:
            glass_card(
                f"<div style='font-weight:700;color:{_class_colors[cls_id]};margin-bottom:0.5rem;'>"
                f"{_class_names[cls_id]}</div>"
                + "".join(
                    f"<div style='display:flex;justify-content:space-between;padding:0.3rem 0;"
                    f"border-bottom:1px solid rgba(255,255,255,0.04);'>"
                    f"<span style='color:#94a3b8;font-size:0.85rem;'>{n}</span>"
                    f"<span style='font-weight:600;font-size:0.85rem;'>{r*100:.1f}%</span></div>"
                    for n, r in _cls_data
                )
            )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRAINING TIME COMPARISON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("---")
section_title("Training Time Comparison", icon="⏱️")

_times = [(n, m.get("training_time_sec", 0)) for n, m in _scored.items()]
_times.sort(key=lambda x: x[1], reverse=True)

fig_time = go.Figure(go.Bar(
    y=[t[0] for t in _times], x=[t[1] for t in _times],
    orientation="h",
    marker_color=ACCENT_CYAN,
    text=[f"{t[1]:.1f}s" for t in _times],
    textposition="auto",
))
apply_theme(fig_time, title="Training Time (seconds)", height=max(250, len(_times) * 50),
            margin=dict(l=140))
st.plotly_chart(fig_time, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FEATURE IMPORTANCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("---")
section_title("Global Feature Importance", icon="🔑")

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
            _features = np.asarray(_vectorizer.get_feature_names_out())

            _coef = None
            if hasattr(_classifier, "coef_"):
                _coef = np.asarray(_classifier.coef_)
            elif hasattr(_classifier, "feature_importances_"):
                _fi = np.asarray(_classifier.feature_importances_)
                _top = _fi.argsort()[-20:][::-1]
                fig_fi = go.Figure(go.Bar(
                    x=_fi[_top], y=_features[_top], orientation="h",
                    marker_color=ACCENT_BLUE,
                ))
                apply_theme(fig_fi, title="Top 20 Important Features", height=500, margin=dict(l=160))
                fig_fi.update_layout(yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_fi, use_container_width=True)

            if _coef is not None:
                _classes = getattr(_classifier, "classes_", [0, 1, 2])
                _pos_idx = list(_classes).index(2) if 2 in list(_classes) else -1
                _neg_idx = list(_classes).index(0) if 0 in list(_classes) else 0

                fi1, fi2 = st.columns(2)
                with fi1:
                    st.markdown("**Top 20 Words → Positive**")
                    _pc = _coef[_pos_idx] if _coef.ndim > 1 and _pos_idx >= 0 else _coef.ravel()
                    _tp = _pc.argsort()[-20:][::-1]
                    fig_p = go.Figure(go.Bar(x=_pc[_tp], y=_features[_tp], orientation="h",
                                            marker_color=POSITIVE_COLOR))
                    apply_theme(fig_p, height=500, margin=dict(l=160))
                    fig_p.update_layout(yaxis=dict(autorange="reversed"))
                    st.plotly_chart(fig_p, use_container_width=True)

                with fi2:
                    st.markdown("**Top 20 Words → Negative**")
                    _nc = _coef[_neg_idx] if _coef.ndim > 1 and _neg_idx >= 0 else -_coef.ravel()
                    _tn = _nc.argsort()[-20:][::-1]
                    fig_n = go.Figure(go.Bar(x=_nc[_tn], y=_features[_tn], orientation="h",
                                            marker_color=NEGATIVE_COLOR))
                    apply_theme(fig_n, height=500, margin=dict(l=160))
                    fig_n.update_layout(yaxis=dict(autorange="reversed"))
                    st.plotly_chart(fig_n, use_container_width=True)

    except Exception as exc:
        st.info(f"Feature importance unavailable: {exc}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODEL INSIGHTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("---")
section_title("Model Insights", icon="💡")

i1, i2, i3 = st.columns(3)
with i1:
    glass_card(
        "<h4 style='font-size:0.95rem;margin-bottom:0.4rem;'>Best Overall</h4>"
        f"<p style='color:#94a3b8;font-size:0.85rem;line-height:1.6;'>"
        f"<b style='color:#f1f5f9;'>{_best_name}</b> achieves the highest Macro F1 ({_best_f1:.4f}), "
        f"making it the best choice for balanced multi-class prediction.</p>"
    )
with i2:
    glass_card(
        "<h4 style='font-size:0.95rem;margin-bottom:0.4rem;'>Neutral Class</h4>"
        "<p style='color:#94a3b8;font-size:0.85rem;line-height:1.6;'>"
        "The Neutral class is hardest to classify due to semantic ambiguity. "
        "Reviews like 'It's okay' or 'Average product' overlap with both Positive and Negative patterns.</p>"
    )
with i3:
    glass_card(
        "<h4 style='font-size:0.95rem;margin-bottom:0.4rem;'>Speed vs Accuracy</h4>"
        "<p style='color:#94a3b8;font-size:0.85rem;line-height:1.6;'>"
        "Linear models (SVC, LR) offer the best accuracy-to-speed ratio. "
        "Random Forest provides moderate accuracy but at significantly higher training cost.</p>"
    )