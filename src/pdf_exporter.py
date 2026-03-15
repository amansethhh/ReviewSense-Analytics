"""PDF export helpers for ReviewSense Analytics."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_FIGURES_PATH = PROJECT_ROOT / "reports" / "figures"

NAVY = (26, 26, 46)
WHITE = (255, 255, 255)
TEXT_DARK = (35, 38, 52)
LIGHT_GRAY = (242, 244, 247)
BORDER_GRAY = (196, 201, 208)
SOFT_ROW = (249, 250, 252)
GREEN = (0, 200, 81)
RED = (255, 75, 75)
ORANGE = (255, 165, 0)


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _sentiment_color(label_name: str) -> tuple[int, int, int]:
    normalized_label = str(label_name).strip().lower()
    if normalized_label == "positive":
        return GREEN
    if normalized_label == "negative":
        return RED
    return ORANGE


def _init_pdf() -> FPDF:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)
    return pdf


def _header_block(pdf: FPDF, subtitle: str) -> None:
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, pdf.w, 34, style="F")

    pdf.set_xy(15, 10)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 8, "ReviewSense Analytics", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"{_timestamp()} | {subtitle}", new_x="LMARGIN", new_y="NEXT")


def _section_title(pdf: FPDF, title: str, y_gap: float = 6) -> None:
    pdf.ln(y_gap)
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")


def _safe_bytes_output(pdf: FPDF) -> bytes:
    output = pdf.output()
    if isinstance(output, (bytes, bytearray)):
        return bytes(output)
    return str(output).encode("latin-1")


def _positive_negative_words(lime_words: list[tuple[str, float]]) -> tuple[list[str], list[str]]:
    positive_words = [word for word, weight in lime_words if weight > 0][:8]
    negative_words = [word for word, weight in lime_words if weight < 0][:8]
    return positive_words, negative_words


def generate_single_report(review_text, prediction_result, lime_words, aspects_df, sarcasm_result) -> bytes:
    """Generate PDF for single review analysis."""

    pdf = _init_pdf()

    # Page 1
    pdf.add_page()
    _header_block(pdf, "Single Review Analysis Report")

    _section_title(pdf, "Review Text", y_gap=12)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.set_draw_color(*BORDER_GRAY)
    pdf.set_text_color(*TEXT_DARK)
    pdf.multi_cell(
        0,
        7,
        txt=str(review_text or "No review text provided."),
        border=1,
        fill=True,
    )

    # Page 2
    pdf.add_page()
    _header_block(pdf, "Single Review Analysis Report")

    label_name = prediction_result.get("label_name", "Neutral")
    confidence = float(prediction_result.get("confidence", 0.0))
    polarity = float(prediction_result.get("polarity", 0.0))
    subjectivity = float(prediction_result.get("subjectivity", 0.0))
    label_color = _sentiment_color(label_name)

    _section_title(pdf, "Sentiment Result", y_gap=14)
    pdf.set_text_color(*label_color)
    pdf.set_font("Helvetica", "B", 26)
    pdf.cell(0, 15, str(label_name), align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Confidence", new_x="LMARGIN", new_y="NEXT")

    bar_x = pdf.l_margin
    bar_y = pdf.get_y() + 2
    bar_width = pdf.w - pdf.l_margin - pdf.r_margin
    bar_height = 10
    pdf.set_fill_color(226, 229, 235)
    pdf.rect(bar_x, bar_y, bar_width, bar_height, style="F")
    pdf.set_fill_color(*label_color)
    pdf.rect(bar_x, bar_y, bar_width * max(0.0, min(confidence, 1.0)), bar_height, style="F")
    pdf.set_draw_color(*BORDER_GRAY)
    pdf.rect(bar_x, bar_y, bar_width, bar_height)
    pdf.ln(16)

    pdf.set_font("Helvetica", "", 12)
    pdf.cell(
        0,
        8,
        f"Polarity: {polarity:.2f} | Subjectivity: {subjectivity:.2f}",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Sarcasm Status", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    sarcasm_detected = bool(sarcasm_result.get("is_sarcastic", False))
    sarcasm_color = RED if sarcasm_detected else GREEN
    sarcasm_text = (
        f"Detected | Severity: {sarcasm_result.get('severity', 'unknown')} | "
        f"Confidence: {float(sarcasm_result.get('confidence', 0.0)):.2f}"
        if sarcasm_detected
        else "No sarcasm indicators detected."
    )
    if sarcasm_detected:
        pdf.set_fill_color(250, 239, 239)
    else:
        pdf.set_fill_color(235, 248, 240)
    pdf.set_draw_color(*sarcasm_color)
    pdf.set_text_color(*TEXT_DARK)
    pdf.multi_cell(0, 8, txt=sarcasm_text, border=1, fill=True)
    sarcasm_reason = sarcasm_result.get("reason")
    if sarcasm_reason:
        pdf.ln(2)
        pdf.set_font("Helvetica", "I", 10)
        pdf.multi_cell(0, 6, txt=f"Reason: {sarcasm_reason}")

    # Page 3
    pdf.add_page()
    _header_block(pdf, "Single Review Analysis Report")
    _section_title(pdf, "Aspect Analysis", y_gap=12)

    aspect_table = aspects_df.copy() if isinstance(aspects_df, pd.DataFrame) else pd.DataFrame()
    if aspect_table.empty:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*TEXT_DARK)
        pdf.multi_cell(0, 8, txt="No aspect analysis data available.", border=1, fill=True)
    else:
        aspect_table = aspect_table.loc[:, ["Aspect", "Sentiment", "Polarity", "Subjectivity"]].head(14)
        headers = ["Aspect", "Sentiment", "Polarity", "Subjectivity"]
        widths = [70, 40, 35, 35]

        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 10)
        for header, width in zip(headers, widths):
            pdf.cell(width, 8, header, border=1, align="C", fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*TEXT_DARK)
        for row_index, (_, row) in enumerate(aspect_table.iterrows()):
            fill_color = LIGHT_GRAY if row_index % 2 == 0 else SOFT_ROW
            pdf.set_fill_color(*fill_color)
            pdf.cell(widths[0], 8, str(row["Aspect"])[:32], border=1, fill=True)
            pdf.cell(widths[1], 8, str(row["Sentiment"]), border=1, fill=True)
            pdf.cell(widths[2], 8, f"{float(row['Polarity']):.2f}", border=1, align="C", fill=True)
            pdf.cell(widths[3], 8, f"{float(row['Subjectivity']):.2f}", border=1, align="C", fill=True)
            pdf.ln()

    positive_words, negative_words = _positive_negative_words(list(lime_words or []))
    _section_title(pdf, "Key Words", y_gap=10)

    column_width = (pdf.w - pdf.l_margin - pdf.r_margin - 6) / 2
    current_y = pdf.get_y()

    pdf.set_xy(pdf.l_margin, current_y)
    pdf.set_fill_color(234, 249, 240)
    pdf.set_draw_color(*GREEN)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*GREEN)
    pdf.multi_cell(column_width, 8, "Positive Words", border=1, fill=True)

    pdf.set_xy(pdf.l_margin + column_width + 6, current_y)
    pdf.set_fill_color(253, 238, 238)
    pdf.set_draw_color(*RED)
    pdf.set_text_color(*RED)
    pdf.multi_cell(column_width, 8, "Negative Words", border=1, fill=True)

    body_y = max(pdf.get_y(), current_y + 8)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*TEXT_DARK)

    pdf.set_xy(pdf.l_margin, body_y)
    pdf.set_fill_color(250, 252, 251)
    pdf.multi_cell(
        column_width,
        7,
        ", ".join(positive_words) if positive_words else "No strong positive keywords detected.",
        border=1,
        fill=True,
    )

    pdf.set_xy(pdf.l_margin + column_width + 6, body_y)
    pdf.set_fill_color(252, 249, 249)
    pdf.multi_cell(
        column_width,
        7,
        ", ".join(negative_words) if negative_words else "No strong negative keywords detected.",
        border=1,
        fill=True,
    )

    # Page 4
    pdf.add_page()
    _header_block(pdf, "Single Review Analysis Report")
    pdf.set_y(120)
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Group 19", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 13)
    pdf.cell(0, 8, "College Name", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 12)
    pdf.cell(0, 8, "Generated by ReviewSense Analytics", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(12)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generated on {_timestamp()}", align="C")

    return _safe_bytes_output(pdf)


def generate_bulk_report(filename, total, pos, neg, neu, recommendation_score, summary_text) -> bytes:
    """Generate summary PDF for bulk analysis."""

    pdf = _init_pdf()
    pdf.add_page()
    _header_block(pdf, "Bulk Analysis Summary Report")

    _section_title(pdf, "File Statistics", y_gap=12)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*TEXT_DARK)
    stats_rows = [
        ("Filename", str(filename)),
        ("Total Reviews", str(total)),
        ("Positive", str(pos)),
        ("Negative", str(neg)),
        ("Neutral", str(neu)),
        ("Recommendation Score", f"{float(recommendation_score):.1f}"),
        ("Generated At", _timestamp()),
    ]
    for label, value in stats_rows:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(52, 8, f"{label}:", border=0)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, value, new_x="LMARGIN", new_y="NEXT")

    chart_path: str | None = None
    try:
        REPORTS_FIGURES_PATH.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(suffix=".png", delete=False) as temp_chart:
            chart_path = temp_chart.name

        figure, axis = plt.subplots(figsize=(4.4, 4.4))
        sentiment_values = [max(pos, 0), max(neg, 0), max(neu, 0)]
        if sum(sentiment_values) > 0:
            axis.pie(
                sentiment_values,
                labels=["Positive", "Negative", "Neutral"],
                colors=["#00c851", "#ff4b4b", "#ffa500"],
                autopct="%1.1f%%",
                startangle=90,
            )
            axis.set_title("Sentiment Distribution")
        else:
            axis.text(0.5, 0.5, "No sentiment data", ha="center", va="center", fontsize=14)
            axis.axis("off")
        axis.axis("equal")
        figure.savefig(chart_path, dpi=220, bbox_inches="tight", facecolor="white")
        plt.close(figure)

        _section_title(pdf, "Sentiment Distribution", y_gap=10)
        pdf.image(chart_path, x=45, w=120)
    finally:
        if "figure" in locals():
            plt.close(figure)

    _section_title(pdf, "AI Summary", y_gap=14)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.set_draw_color(*BORDER_GRAY)
    pdf.multi_cell(
        0,
        7,
        txt=str(summary_text or "No summary available."),
        border=1,
        fill=True,
    )

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*TEXT_DARK)
    pdf.cell(
        0,
        8,
        f"Recommendation Score: {float(recommendation_score):.1f}/100",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    report_bytes = _safe_bytes_output(pdf)

    if chart_path:
        try:
            Path(chart_path).unlink(missing_ok=True)
        except Exception:
            pass

    return report_bytes


def export_report(data: dict[str, Any], output_path: str | Path) -> Path:
    """Compatibility wrapper for the existing Streamlit app."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if data.get("bulk_results"):
        bulk_df = pd.DataFrame(data["bulk_results"])
        sentiment_column = "Sentiment" if "Sentiment" in bulk_df.columns else None
        total = len(bulk_df)
        pos = int((bulk_df[sentiment_column] == "Positive").sum()) if sentiment_column else 0
        neg = int((bulk_df[sentiment_column] == "Negative").sum()) if sentiment_column else 0
        neu = int((bulk_df[sentiment_column] == "Neutral").sum()) if sentiment_column else max(total - pos - neg, 0)
        recommendation_score = float((pos / total) * 100.0) if total else 0.0
        summary_text = data.get(
            "summary_text",
            "Bulk review analysis completed successfully. See the attached statistics for the sentiment breakdown.",
        )
        pdf_bytes = generate_bulk_report(
            filename=data.get("filename", "uploaded_reviews.csv"),
            total=total,
            pos=pos,
            neg=neg,
            neu=neu,
            recommendation_score=recommendation_score,
            summary_text=summary_text,
        )
    else:
        pdf_bytes = generate_single_report(
            review_text=data.get("review_text", ""),
            prediction_result=data.get("result", {}),
            lime_words=data.get("word_weights", []),
            aspects_df=data.get("aspects_df", pd.DataFrame(columns=["Aspect", "Sentiment", "Polarity", "Subjectivity"])),
            sarcasm_result=data.get("sarcasm_result", {}),
        )

    output_path.write_bytes(pdf_bytes)
    return output_path
