"""
src/pdf_exporter.py
-------------------
PDF report generation module using fpdf2.

Responsibilities:
- Compile analysis results, charts, and metrics into a formatted PDF
- Support custom branding (logo, colours, section headers)
- Expose an export_report(data, output_path) function
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def export_report(data: dict[str, Any], output_path: str | Path) -> Path:
    """Generate a PDF report from *data* and write it to *output_path*.

    Parameters
    ----------
    data:
        Dictionary of report data.  Recognised keys:
        - ``"review_text"`` (str) — the analysed review.
        - ``"result"`` (dict) — prediction result from ``predict_sentiment()``.
        - ``"word_weights"`` (list) — LIME word weights.
        - ``"bulk_results"`` (list[dict]) — rows from bulk analysis.
    output_path:
        Destination file path (will be created / overwritten).

    Returns
    -------
    Path
        The resolved path of the generated PDF file.
    """
    from fpdf import FPDF

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Header ──────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(0, 229, 255)
    pdf.cell(0, 12, "ReviewSense Analytics - Report", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_draw_color(0, 229, 255)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

    # ── Single review result ────────────────────────────────────────────────
    result = data.get("result")
    review_text = data.get("review_text", "")

    if result and review_text:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(232, 234, 246)
        pdf.cell(0, 8, "Sentiment Analysis Result", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(158, 158, 184)
        pdf.multi_cell(0, 6, f"Review: {review_text[:300]}")
        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 200, 81)
        label_name = result.get("label_name", "Unknown")
        confidence = result.get("confidence", 0.0)
        polarity = result.get("polarity", 0.0)
        subjectivity = result.get("subjectivity", 0.0)
        pdf.cell(0, 7, f"Sentiment: {label_name}  |  Confidence: {confidence * 100:.1f}%", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(232, 234, 246)
        pdf.cell(0, 6, f"Polarity: {polarity:.4f}  |  Subjectivity: {subjectivity:.4f}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        word_weights = data.get("word_weights", [])
        if word_weights:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(232, 234, 246)
            pdf.cell(0, 7, "Top LIME Feature Contributions:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            for word, weight in word_weights[:10]:
                direction = "+" if weight >= 0 else ""
                pdf.cell(0, 5, f"  {word}: {direction}{weight:.4f}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

    # ── Bulk results summary ────────────────────────────────────────────────
    bulk_results = data.get("bulk_results", [])
    if bulk_results:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(232, 234, 246)
        pdf.cell(0, 8, "Bulk Analysis Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        total = len(bulk_results)
        pos = sum(1 for r in bulk_results if r.get("Sentiment") == "Positive")
        neg = sum(1 for r in bulk_results if r.get("Sentiment") == "Negative")
        neu = total - pos - neg

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(232, 234, 246)
        pdf.cell(0, 6, f"Total reviews: {total}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Positive: {pos} ({pos / total * 100:.1f}%)", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Negative: {neg} ({neg / total * 100:.1f}%)", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Neutral:  {neu} ({neu / total * 100:.1f}%)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Sample rows table
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(158, 158, 184)
        pdf.cell(110, 6, "Review (truncated)", border=1)
        pdf.cell(30, 6, "Sentiment", border=1)
        pdf.cell(30, 6, "Confidence", border=1, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(232, 234, 246)
        for row in bulk_results[:50]:
            text_preview = str(row.get(next(iter(row), ""), ""))[:60]
            sentiment = str(row.get("Sentiment", ""))
            confidence_val = str(row.get("Confidence", ""))
            pdf.cell(110, 5, text_preview, border=1)
            pdf.cell(30, 5, sentiment, border=1)
            pdf.cell(30, 5, confidence_val, border=1, new_x="LMARGIN", new_y="NEXT")

    # ── Footer ───────────────────────────────────────────────────────────────
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 130)
    pdf.cell(0, 5, "Generated by ReviewSense Analytics - Group 19", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(output_path))
    return output_path

