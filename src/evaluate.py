"""Evaluation visualizations for ReviewSense Analytics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.metrics import auc, roc_curve
from sklearn.preprocessing import label_binarize

from src.config import LABEL_MAP

CLASS_LABELS = sorted(LABEL_MAP.keys())
CLASS_NAMES = [LABEL_MAP[label] for label in CLASS_LABELS]


def _resolve_display_labels(labels: Sequence[int | str]) -> list[str]:
    resolved_labels: list[str] = []

    for label in labels:
        if isinstance(label, str):
            resolved_labels.append(label)
        else:
            resolved_labels.append(LABEL_MAP.get(int(label), str(label)))

    return resolved_labels


def _load_results_json(results_json_path: str | Path) -> dict:
    path = Path(results_json_path)
    if not path.exists():
        raise FileNotFoundError(f"Results JSON not found: {path}")

    with path.open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def _extract_score_matrix(model, X_test: Sequence[str], class_labels: Sequence[int]) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        scores = model.predict_proba(X_test)
    elif hasattr(model, "decision_function"):
        scores = model.decision_function(X_test)
    else:
        raise ValueError(f"Model {type(model).__name__} does not expose predict_proba or decision_function.")

    scores = np.asarray(scores)
    if scores.ndim == 1:
        scores = scores.reshape(-1, 1)

    model_classes = getattr(model, "classes_", None)
    if model_classes is None and hasattr(model, "named_steps"):
        classifier = model.named_steps.get("clf")
        model_classes = getattr(classifier, "classes_", None)

    if len(class_labels) == 2 and scores.shape[1] == 1:
        scores = np.column_stack([-scores[:, 0], scores[:, 0]])
        return scores

    if model_classes is None:
        if scores.shape[1] != len(class_labels):
            raise ValueError("Unable to align model scores to class labels.")
        return scores

    aligned_scores = np.zeros((scores.shape[0], len(class_labels)))
    label_to_index = {label: index for index, label in enumerate(class_labels)}

    for score_index, class_label in enumerate(model_classes):
        target_index = label_to_index.get(int(class_label))
        if target_index is not None:
            aligned_scores[:, target_index] = scores[:, score_index]

    return aligned_scores


def plot_accuracy_comparison(results_json_path) -> go.Figure:
    """Load model_results.json, return Plotly grouped bar chart showing Accuracy + F1 for each model."""

    results = _load_results_json(results_json_path)
    model_rows = []

    for model_name, metrics in results.items():
        if not isinstance(metrics, dict) or "accuracy" not in metrics or "f1" not in metrics:
            continue
        model_rows.append(
            {
                "model": model_name,
                "accuracy": float(metrics["accuracy"]),
                "f1": float(metrics["f1"]),
            }
        )

    if not model_rows:
        raise ValueError("No model metrics were found in the results JSON.")

    metrics_df = pd.DataFrame(model_rows)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Accuracy",
            x=metrics_df["model"],
            y=metrics_df["accuracy"],
            marker_color="#3ba7ff",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Macro F1",
            x=metrics_df["model"],
            y=metrics_df["f1"],
            marker_color="#00c851",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        barmode="group",
        title="Model Accuracy and F1 Comparison",
        xaxis_title="Model",
        yaxis_title="Score",
        yaxis=dict(range=[0, 1]),
    )

    return fig


def plot_confusion_matrix(cm_array, model_name, labels) -> go.Figure:
    """Return Plotly heatmap of confusion matrix with Negative/Neutral/Positive labels."""

    matrix = np.asarray(cm_array)
    if matrix.ndim != 2:
        raise ValueError("Confusion matrix must be a 2D array.")

    display_labels = _resolve_display_labels(labels)
    if matrix.shape[0] != len(display_labels) or matrix.shape[1] != len(display_labels):
        raise ValueError("Confusion matrix shape must match the number of provided labels.")

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=display_labels,
            y=display_labels,
            colorscale="Blues",
            text=matrix,
            texttemplate="%{text}",
            hovertemplate="True: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        title=f"{model_name} Confusion Matrix",
        xaxis_title="Predicted Label",
        yaxis_title="True Label",
        yaxis_autorange="reversed",
    )

    return fig


def plot_roc_curves(models_dict, X_test, y_test) -> go.Figure:
    """Compute one-vs-rest ROC curves for all models and overlay them in a Plotly figure."""

    if not isinstance(models_dict, Mapping) or not models_dict:
        raise ValueError("models_dict must be a non-empty mapping of model names to fitted models.")

    y_test_array = np.asarray(y_test, dtype=int)
    y_test_binary = label_binarize(y_test_array, classes=CLASS_LABELS)

    fig = go.Figure()
    colors = ["#3ba7ff", "#00c851", "#ffa500", "#ff4b4b", "#a56eff"]

    for index, (model_name, model) in enumerate(models_dict.items()):
        score_matrix = _extract_score_matrix(model, X_test, CLASS_LABELS)
        fpr, tpr, _ = roc_curve(y_test_binary.ravel(), score_matrix.ravel())
        roc_auc = auc(fpr, tpr)

        fig.add_trace(
            go.Scatter(
                x=fpr,
                y=tpr,
                mode="lines",
                name=f"{model_name} (AUC={roc_auc:.3f})",
                line=dict(color=colors[index % len(colors)], width=2.5),
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Chance",
            line=dict(color="#cccccc", dash="dash"),
        )
    )
    fig.update_layout(
        template="plotly_dark",
        title="One-vs-Rest ROC Curves",
        xaxis_title="False Positive Rate",
        yaxis_title="True Positive Rate",
        yaxis=dict(range=[0, 1.05]),
        xaxis=dict(range=[0, 1]),
    )

    return fig


def plot_sentiment_trend(amazon_df) -> go.Figure:
    """Group reviews by month and plot the positive sentiment share over time."""

    required_columns = {"text", "label", "time"}
    missing_columns = required_columns.difference(amazon_df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"amazon_df is missing required columns: {missing}")

    trend_df = amazon_df.copy()
    trend_df["time"] = pd.to_datetime(trend_df["time"], errors="coerce")
    trend_df["label"] = pd.to_numeric(trend_df["label"], errors="coerce")
    trend_df = trend_df.dropna(subset=["time", "label"])

    if trend_df.empty:
        raise ValueError("No valid rows available after parsing the time and label columns.")

    trend_df["period"] = trend_df["time"].dt.to_period("M").dt.to_timestamp()

    monthly_trend = (
        trend_df.groupby("period")
        .agg(
            review_count=("text", "size"),
            positive_reviews=("label", lambda values: int((values == 2).sum())),
        )
        .reset_index()
    )
    monthly_trend["positive_pct"] = (
        monthly_trend["positive_reviews"] / monthly_trend["review_count"] * 100.0
    )

    fig = go.Figure(
        data=[
            go.Scatter(
                x=monthly_trend["period"],
                y=monthly_trend["positive_pct"],
                mode="lines+markers",
                line=dict(color="#00c851", width=3),
                marker=dict(size=8),
                name="Positive %",
            )
        ]
    )
    fig.update_layout(
        template="plotly_dark",
        title="Monthly Positive Sentiment Trend",
        xaxis_title="Month",
        yaxis_title="Positive Reviews (%)",
        yaxis=dict(range=[0, 100]),
    )

    changes = monthly_trend["positive_pct"].diff()
    if changes.notna().any():
        change_index = changes.abs().idxmax()
        change_value = float(changes.loc[change_index])
        change_type = "rise" if change_value >= 0 else "drop"
        change_row = monthly_trend.loc[change_index]
        fig.add_annotation(
            x=change_row["period"],
            y=change_row["positive_pct"],
            text=f"Biggest {change_type}: {change_value:+.1f} pp",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#ffffff",
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="#ffffff",
        )

    return fig
