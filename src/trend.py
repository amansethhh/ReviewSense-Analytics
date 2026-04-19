"""Rolling trend calculation for ReviewSense Analytics.

ADD-ON 8: Replaces the static batch-based trend chart with a rolling
window approach that eliminates CSV ordering artifacts.

Uses LABEL_MAP integers: 0=Negative, 1=Neutral, 2=Positive.
"""

from __future__ import annotations


def compute_rolling_trend(results: list[dict],
                           window: int = 40) -> list[dict]:
    """Compute sentiment trend using a rolling window.

    Step size = window // 2 (50% overlap) for smooth trend visualization.
    Returns one data point per step.

    Args:
        results: List of result dicts, each with a "label" key (int 0/1/2).
        window: Rolling window size (default 40).

    Returns:
        List of trend data points with label, positive/negative/neutral pct.
    """
    if not results or len(results) < window:
        # Not enough data for rolling window — return single point
        if results:
            total = len(results)
            pos = sum(1 for r in results if r.get("label") == 2)
            neg = sum(1 for r in results if r.get("label") == 0)
            neu = sum(1 for r in results if r.get("label") == 1)
            return [{
                "window_start": 1,
                "window_end": total,
                "label": f"Reviews 1–{total}",
                "positive_pct": round(pos / total * 100, 1),
                "negative_pct": round(neg / total * 100, 1),
                "neutral_pct": round(neu / total * 100, 1),
            }]
        return []

    trend = []
    step = window // 2  # 50% overlap = step of 20 for window=40

    for i in range(0, len(results) - window + 1, step):
        window_slice = results[i:i + window]
        total = len(window_slice)

        pos = sum(1 for r in window_slice if r.get("label") == 2)
        neg = sum(1 for r in window_slice if r.get("label") == 0)
        neu = sum(1 for r in window_slice if r.get("label") == 1)

        trend.append({
            "window_start": i + 1,
            "window_end": i + window,
            "label": f"Reviews {i+1}–{i+window}",
            "positive_pct": round(pos / total * 100, 1),
            "negative_pct": round(neg / total * 100, 1),
            "neutral_pct": round(neu / total * 100, 1),
        })

    return trend
