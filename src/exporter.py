"""Centralized export module for ReviewSense Analytics.

Single function `render_export_buttons()` renders a 4-column export row
(CSV, JSON, PDF, Excel) for any page. NO page-specific export code needed.
"""

from __future__ import annotations

import io
import json
import tempfile
import os
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


def render_export_buttons(
    df: pd.DataFrame,
    filename_prefix: str = "reviewsense",
    pdf_data: dict[str, Any] | None = None,
) -> None:
    """Render standardized 4-column export row: CSV, JSON, PDF, Excel.

    Args:
        df: DataFrame to export.
        filename_prefix: Base name for exported files.
        pdf_data: Optional dict passed to `export_report()` for PDF.
                  If None, a basic bulk export is generated from `df`.
    """
    with st.container():
        st.markdown(
            '<div class="glass-card-header">'
            '<div class="section-title">📥 Export Results</div>'
            '<div class="section-subtitle">Download in multiple formats</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        e1, e2, e3, e4 = st.columns(4)

        # CSV
        with e1:
            st.download_button(
                "📊 CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"{filename_prefix}.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"{filename_prefix}_csv",
            )

        # PDF
        with e2:
            try:
                from src.pdf_exporter import export_report

                data_for_pdf = pdf_data or {"bulk_results": df.to_dict(orient="records")}
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as _t:
                    _tp = _t.name
                try:
                    export_report(data_for_pdf, _tp)
                    with open(_tp, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        "📄 PDF",
                        data=pdf_bytes,
                        file_name=f"{filename_prefix}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"{filename_prefix}_pdf",
                    )
                finally:
                    if os.path.exists(_tp):
                        os.unlink(_tp)
            except Exception:
                st.button(
                    "📄 PDF",
                    disabled=True,
                    use_container_width=True,
                    key=f"{filename_prefix}_pdf_dis",
                )

        # JSON
        with e3:
            st.download_button(
                "📋 JSON",
                data=df.to_json(orient="records", indent=2),
                file_name=f"{filename_prefix}.json",
                mime="application/json",
                use_container_width=True,
                key=f"{filename_prefix}_json",
            )

        # Excel
        with e4:
            try:
                buf = io.BytesIO()
                df.to_excel(buf, index=False, engine="openpyxl")
                st.download_button(
                    "📗 Excel",
                    data=buf.getvalue(),
                    file_name=f"{filename_prefix}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"{filename_prefix}_xlsx",
                )
            except Exception:
                st.button(
                    "📗 Excel",
                    disabled=True,
                    use_container_width=True,
                    key=f"{filename_prefix}_xl_dis",
                )

        st.markdown('<div class="card-bottom-border"></div>', unsafe_allow_html=True)
