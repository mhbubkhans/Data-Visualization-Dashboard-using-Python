"""
utils.py
--------
Helper functions: export, session-state management, UI utilities.
"""

import io
from typing import Optional

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------

def init_session_state() -> None:
    """Initialise all required session state keys on first run."""
    defaults = {
        "df_raw": None,          # Original loaded DataFrame
        "df_clean": None,        # After cleaning steps
        "df_filtered": None,     # After sidebar filters
        "filename": "",
        "clean_steps_log": [],
        # Sidebar filter state
        "filter_date_col": None,
        "filter_date_range": None,
        "filter_cat": {},
        "filter_num": {},
        "filter_text": "",
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def reset_filters() -> None:
    """Clear all sidebar filter state keys."""
    keys = [
        "filter_date_col", "filter_date_range",
        "filter_cat", "filter_num", "filter_text",
    ]
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def reset_all() -> None:
    """Full reset — removes all session state so the user can start fresh."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialise a DataFrame to CSV bytes for st.download_button."""
    return df.to_csv(index=False).encode("utf-8")


def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialise a DataFrame to Excel bytes for st.download_button."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return buffer.getvalue()


def figure_to_png_bytes(fig) -> Optional[bytes]:
    """
    Convert a Plotly figure to PNG bytes.
    Requires kaleido to be installed; returns None on failure.
    """
    try:
        return fig.to_image(format="png", scale=2)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# UI component helpers
# ---------------------------------------------------------------------------

def kpi_card(label: str, value: str, emoji: str = "📊") -> None:
    """Render a single KPI card using Streamlit metric."""
    st.metric(label=f"{emoji}  {label}", value=value)


def render_kpi_row(kpis: dict, emojis: Optional[dict] = None) -> None:
    """Render a row of KPI cards in equal-width columns."""
    default_emojis = {
        "Total Rows": "📋",
        "Total Columns": "📐",
        "Total": "💰",
        "Average": "📊",
        "Max": "⬆️",
        "Min": "⬇️",
        "Std Dev": "📉",
        "Missing Cells": "❓",
        "Duplicate Rows": "🔁",
    }
    emoji_map = {**default_emojis, **(emojis or {})}

    items = list(kpis.items())
    cols = st.columns(min(len(items), 4))
    for i, (label, value) in enumerate(items):
        with cols[i % len(cols)]:
            em = emoji_map.get(label, "📌")
            kpi_card(label, str(value), em)


def info_box(text: str, kind: str = "info") -> None:
    """Display a styled info, success, or warning box."""
    if kind == "success":
        st.success(text)
    elif kind == "warning":
        st.warning(text)
    elif kind == "error":
        st.error(text)
    else:
        st.info(text)


def section_header(title: str, subtitle: str = "") -> None:
    """Render a styled section header."""
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)
    st.divider()


def no_data_warning() -> None:
    """Displayed whenever no data is loaded yet."""
    st.info(
        "**No data loaded yet.** "
        "Please upload a CSV or Excel file, or click 'Load Sample Data' to explore a demo dataset.",
        icon="📂",
    )
