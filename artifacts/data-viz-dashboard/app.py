"""
app.py
------
Main Streamlit entry point for the Data Visualization Dashboard.
Provides multi-page navigation via st.navigation.
"""

import streamlit as st

# Must be first Streamlit call
st.set_page_config(
    page_title="Data Viz Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

import numpy as np
import pandas as pd
import plotly.express as px

from data_processing import (
    apply_cleaning_steps,
    apply_filters,
    get_categorical_columns,
    get_date_columns,
    get_numeric_columns,
    load_file,
    load_sample_data,
    memory_usage_mb,
    missing_summary,
    validate_dataframe,
)
from insights import (
    category_comparison,
    compute_kpis,
    flag_outliers,
    generate_insights,
    trend_analysis,
)
from utils import (
    df_to_csv_bytes,
    df_to_excel_bytes,
    figure_to_png_bytes,
    init_session_state,
    no_data_warning,
    render_kpi_row,
    reset_all,
    reset_filters,
    section_header,
)
from visualizations import (
    CHART_REGISTRY,
    area_chart,
    bar_chart,
    box_plot,
    heatmap_chart,
    histogram_chart,
    line_chart,
    pie_chart,
    scatter_chart,
    top_n_bar,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
init_session_state()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _active_df() -> pd.DataFrame | None:
    """Return the most processed DataFrame available."""
    return (
        st.session_state.get("df_filtered")
        or st.session_state.get("df_clean")
        or st.session_state.get("df_raw")
    )


def _safe_col_pick(df: pd.DataFrame, cols: list, label: str, key: str, index: int = 0):
    """Render a selectbox over a list of columns, defaulting to index."""
    if not cols:
        st.warning(f"No {label} columns available.")
        return None
    safe_index = min(index, len(cols) - 1)
    return st.selectbox(label, cols, index=safe_index, key=key)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar():
    """Render the persistent sidebar: branding, dataset info, and filters."""
    with st.sidebar:
        st.markdown("## 📊 DataViz Dashboard")
        st.caption("Upload a file or load the sample dataset to get started.")
        st.divider()

        df = _active_df()
        if df is None:
            st.info("No data loaded.", icon="📂")
            return

        # Dataset info chip
        st.markdown(
            f"**Dataset:** `{st.session_state.get('filename', 'sample_data.csv')}`  \n"
            f"**Shape:** {df.shape[0]:,} rows × {df.shape[1]} cols  \n"
            f"**Memory:** {memory_usage_mb(df):.2f} MB"
        )
        st.divider()

        # ---- Filters ----
        st.markdown("### 🔍 Filters")

        date_cols = get_date_columns(df)
        cat_cols = get_categorical_columns(df)
        num_cols = get_numeric_columns(df)

        # Date range filter
        date_col_choice = None
        if date_cols:
            date_col_choice = st.selectbox("Date column", ["(none)"] + date_cols, key="sb_date_col")
            if date_col_choice != "(none)":
                min_d = df[date_col_choice].min().date()
                max_d = df[date_col_choice].max().date()
                date_range = st.date_input(
                    "Date range",
                    value=(min_d, max_d),
                    min_value=min_d,
                    max_value=max_d,
                    key="sb_date_range",
                )
                st.session_state["filter_date_col"] = date_col_choice
                st.session_state["filter_date_range"] = date_range if len(date_range) == 2 else None
            else:
                st.session_state["filter_date_col"] = None
                st.session_state["filter_date_range"] = None

        # Categorical multi-select filters (up to 3 columns)
        cat_filters = {}
        for col in cat_cols[:3]:
            unique_vals = sorted(df[col].dropna().unique().tolist())
            selected = st.multiselect(f"{col}", unique_vals, key=f"sb_cat_{col}")
            if selected:
                cat_filters[col] = selected
        st.session_state["filter_cat"] = cat_filters

        # Numeric range sliders (up to 2 columns)
        num_filters = {}
        for col in num_cols[:2]:
            col_data = df[col].dropna()
            if col_data.empty:
                continue
            lo, hi = float(col_data.min()), float(col_data.max())
            if lo == hi:
                continue
            chosen = st.slider(
                f"{col} range",
                min_value=lo, max_value=hi,
                value=(lo, hi),
                key=f"sb_num_{col}",
            )
            num_filters[col] = chosen
        st.session_state["filter_num"] = num_filters

        # Text search
        text_q = st.text_input("🔎 Text search (all columns)", key="sb_text")
        st.session_state["filter_text"] = text_q

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Reset Filters", use_container_width=True):
                reset_filters()
        with col2:
            if st.button("Clear All", use_container_width=True, type="secondary"):
                reset_all()

        # Apply filters to produce df_filtered
        base = st.session_state.get("df_clean") or st.session_state.get("df_raw")
        if base is not None:
            st.session_state["df_filtered"] = apply_filters(
                base,
                date_col=st.session_state.get("filter_date_col"),
                date_range=st.session_state.get("filter_date_range"),
                cat_filters=st.session_state.get("filter_cat", {}),
                num_filters=st.session_state.get("filter_num", {}),
                text_search=st.session_state.get("filter_text", ""),
            )


# ===========================================================================
# Page 1 — Home / Overview
# ===========================================================================

def page_home():
    section_header("🏠 Home / Overview", "Your all-in-one data analytics dashboard")

    df = _active_df()
    if df is None:
        no_data_warning()
        st.markdown("---")
        st.markdown("### Quick Start")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                """
                **Upload your own data**
                - Go to the **Data Upload & Cleaning** tab
                - Upload a CSV or Excel file
                - Apply optional cleaning steps
                """
            )
        with c2:
            st.markdown(
                """
                **Explore the demo**
                - Click the button below to load a sample dataset
                - Then navigate to **Visualizations** or **Insights**
                """
            )
        if st.button("▶ Load Sample Dataset", type="primary"):
            with st.spinner("Loading sample data..."):
                sample = load_sample_data()
                sample["Date"] = pd.to_datetime(sample["Date"], errors="coerce")
                st.session_state["df_raw"] = sample
                st.session_state["df_clean"] = sample
                st.session_state["filename"] = "sample_data.csv"
            st.rerun()
        return

    # KPIs
    num_cols = get_numeric_columns(df)
    value_col = num_cols[0] if num_cols else None
    kpis = compute_kpis(df, value_col)
    render_kpi_row(kpis)

    st.divider()

    # Quick charts
    col1, col2 = st.columns(2)
    cat_cols = get_categorical_columns(df)
    date_cols = get_date_columns(df)

    with col1:
        if cat_cols and num_cols:
            fig = top_n_bar(df, cat_cols[0], num_cols[0], n=8,
                            title=f"Top 8 {cat_cols[0]} by {num_cols[0]}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add categorical and numeric columns for charts.")

    with col2:
        if date_cols and num_cols:
            trend = trend_analysis(df, date_cols[0], num_cols[0])
            if not trend.empty:
                fig = line_chart(trend, date_cols[0], num_cols[0],
                                 title=f"{num_cols[0]} Over Time")
                st.plotly_chart(fig, use_container_width=True)
        elif cat_cols and num_cols:
            fig = pie_chart(
                df.groupby(cat_cols[0])[num_cols[0]].sum().reset_index(),
                cat_cols[0], num_cols[0],
                title=f"{num_cols[0]} Distribution by {cat_cols[0]}",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Auto insights preview
    st.divider()
    st.markdown("### 💡 Quick Insights")
    insights = generate_insights(df, value_col)
    for ins in insights[:4]:
        st.markdown(f"- {ins}")
    st.caption("See the **Insights & Summary** tab for the full analysis.")


# ===========================================================================
# Page 2 — Data Upload & Cleaning
# ===========================================================================

def page_upload():
    section_header("📂 Data Upload & Cleaning", "Load your data and apply cleaning steps")

    # ---- Upload ----
    st.markdown("#### 1. Load Data")
    col_up, col_sample = st.columns([3, 1])
    with col_up:
        uploaded = st.file_uploader(
            "Upload CSV or Excel",
            type=["csv", "xlsx", "xls"],
            label_visibility="collapsed",
        )
    with col_sample:
        if st.button("📁 Load Sample Data", use_container_width=True):
            with st.spinner("Loading..."):
                sample = load_sample_data()
                sample["Date"] = pd.to_datetime(sample["Date"], errors="coerce")
                st.session_state["df_raw"] = sample
                st.session_state["df_clean"] = sample
                st.session_state["filename"] = "sample_data.csv"
                st.session_state["clean_steps_log"] = []
            st.success("Sample data loaded!", icon="✅")

    if uploaded:
        with st.spinner(f"Reading '{uploaded.name}'..."):
            df, err = load_file(uploaded)
        if err:
            st.error(err)
        else:
            is_valid, warnings = validate_dataframe(df)
            if not is_valid:
                for w in warnings:
                    st.error(w)
            else:
                for w in warnings:
                    st.warning(w)
                # Auto parse dates
                from data_processing import auto_parse_dates
                df = auto_parse_dates(df)
                st.session_state["df_raw"] = df
                st.session_state["df_clean"] = df.copy()
                st.session_state["filename"] = uploaded.name
                st.session_state["clean_steps_log"] = []
                st.success(
                    f"Loaded **{uploaded.name}** — {len(df):,} rows × {len(df.columns)} columns",
                    icon="✅",
                )

    df_raw = st.session_state.get("df_raw")
    if df_raw is None:
        no_data_warning()
        return

    st.divider()
    st.markdown("#### 2. Cleaning Options")

    c1, c2, c3 = st.columns(3)
    with c1:
        missing_strategy = st.selectbox(
            "Missing value strategy",
            ["Keep as-is", "Drop rows", "Fill with Mean", "Fill with Median", "Fill with Mode"],
        )
        deduplicate = st.checkbox("Remove duplicate rows")
    with c2:
        parse_dates = st.checkbox("Auto-parse date columns", value=True)
        convert_nums = st.checkbox("Convert text to numeric where possible")
    with c3:
        remove_outliers = st.checkbox("Remove outliers (IQR method)")

    if st.button("✨ Apply Cleaning", type="primary"):
        with st.spinner("Cleaning..."):
            cleaned, steps = apply_cleaning_steps(
                df_raw,
                missing_strategy=missing_strategy,
                deduplicate=deduplicate,
                parse_dates=parse_dates,
                convert_nums=convert_nums,
                remove_outliers=remove_outliers,
            )
        st.session_state["df_clean"] = cleaned
        st.session_state["df_filtered"] = None
        st.session_state["clean_steps_log"] = steps
        st.success("Cleaning complete!", icon="🧹")

    # Steps applied
    log = st.session_state.get("clean_steps_log", [])
    if log:
        with st.expander("📋 Cleaning log", expanded=False):
            for step in log:
                st.markdown(f"✔ {step}")

    st.divider()
    st.markdown("#### 3. Missing Value Summary")
    df_clean = st.session_state.get("df_clean", df_raw)
    ms = missing_summary(df_clean)
    st.dataframe(ms, use_container_width=True)

    st.divider()
    st.markdown("#### 4. Data Preview")
    n_preview = st.slider("Rows to preview", 5, min(100, len(df_clean)), 10)
    st.dataframe(df_clean.head(n_preview), use_container_width=True)


# ===========================================================================
# Page 3 — Interactive Visualizations
# ===========================================================================

def page_visualizations():
    section_header("📈 Interactive Visualizations", "Explore your data through dynamic charts")

    df = _active_df()
    if df is None:
        no_data_warning()
        return

    num_cols = get_numeric_columns(df)
    cat_cols = get_categorical_columns(df)
    date_cols = get_date_columns(df)
    all_cols = list(df.columns)

    chart_type = st.selectbox(
        "Chart Type",
        list(CHART_REGISTRY.keys()),
        key="viz_chart_type",
    )

    st.divider()

    fig = None

    if chart_type in ("Line Chart", "Area Chart"):
        c1, c2, c3 = st.columns(3)
        with c1:
            x = _safe_col_pick(df, date_cols + cat_cols + num_cols, "X-axis (time or category)", "viz_x")
        with c2:
            y = _safe_col_pick(df, num_cols, "Y-axis (numeric)", "viz_y")
        with c3:
            color = st.selectbox("Color by (optional)", ["(none)"] + cat_cols, key="viz_color")
            color = None if color == "(none)" else color

        if x and y:
            fn = line_chart if chart_type == "Line Chart" else area_chart
            fig = fn(df, x, y, color_col=color, title=f"{chart_type}: {y} by {x}")

    elif chart_type == "Bar Chart":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            x = _safe_col_pick(df, cat_cols + num_cols, "X-axis (category)", "viz_bar_x")
        with c2:
            y = _safe_col_pick(df, num_cols, "Y-axis (numeric)", "viz_bar_y")
        with c3:
            color = st.selectbox("Color by (optional)", ["(none)"] + cat_cols, key="viz_bar_color")
            color = None if color == "(none)" else color
        with c4:
            orientation = st.radio("Orientation", ["Vertical", "Horizontal"], horizontal=True, key="viz_bar_orient")
            orient = "v" if orientation == "Vertical" else "h"

        if x and y:
            # Aggregate before charting
            agg_df = df.groupby(x)[y].sum().reset_index() if color is None else df.groupby([x, color])[y].sum().reset_index()
            fig = bar_chart(agg_df, x, y, color_col=color, orientation=orient,
                            title=f"Bar Chart: {y} by {x}")

    elif chart_type == "Pie Chart":
        c1, c2 = st.columns(2)
        with c1:
            names = _safe_col_pick(df, cat_cols, "Category column", "viz_pie_names")
        with c2:
            values = _safe_col_pick(df, num_cols, "Values column", "viz_pie_vals")
        if names and values:
            agg = df.groupby(names)[values].sum().reset_index()
            fig = pie_chart(agg, names, values, title=f"Pie Chart: {values} by {names}")

    elif chart_type == "Scatter Plot":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            x = _safe_col_pick(df, num_cols, "X-axis", "viz_sc_x")
        with c2:
            y = _safe_col_pick(df, num_cols, "Y-axis", "viz_sc_y", index=1)
        with c3:
            color = st.selectbox("Color by", ["(none)"] + cat_cols, key="viz_sc_color")
            color = None if color == "(none)" else color
        with c4:
            size_col = st.selectbox("Size by (optional)", ["(none)"] + num_cols, key="viz_sc_size")
            size_col = None if size_col == "(none)" else size_col
        if x and y:
            fig = scatter_chart(df, x, y, color_col=color, size_col=size_col,
                                title=f"Scatter: {y} vs {x}")

    elif chart_type == "Histogram":
        c1, c2, c3 = st.columns(3)
        with c1:
            col = _safe_col_pick(df, num_cols, "Column", "viz_hist_col")
        with c2:
            nbins = st.slider("Bins", 5, 100, 30, key="viz_hist_bins")
        with c3:
            color = st.selectbox("Color by (optional)", ["(none)"] + cat_cols, key="viz_hist_color")
            color = None if color == "(none)" else color
        if col:
            fig = histogram_chart(df, col, color_col=color, nbins=nbins,
                                  title=f"Histogram of {col}")

    elif chart_type == "Box Plot":
        c1, c2, c3 = st.columns(3)
        with c1:
            x = _safe_col_pick(df, cat_cols, "X-axis (category)", "viz_box_x")
        with c2:
            y = _safe_col_pick(df, num_cols, "Y-axis (numeric)", "viz_box_y")
        with c3:
            color = st.selectbox("Color by (optional)", ["(none)"] + cat_cols, key="viz_box_color")
            color = None if color == "(none)" else color
        if x and y:
            fig = box_plot(df, x, y, color_col=color, title=f"Box Plot: {y} by {x}")

    elif chart_type == "Correlation Heatmap":
        fig = heatmap_chart(df, title="Correlation Heatmap")

    elif chart_type == "Top-N Bar":
        c1, c2, c3 = st.columns(3)
        with c1:
            group = _safe_col_pick(df, cat_cols, "Group by", "viz_topn_group")
        with c2:
            val = _safe_col_pick(df, num_cols, "Value column", "viz_topn_val")
        with c3:
            n = st.slider("Top N", 3, 30, 10, key="viz_topn_n")
        if group and val:
            fig = top_n_bar(df, group, val, n=n, title=f"Top {n} {group} by {val}")

    if fig:
        st.plotly_chart(fig, use_container_width=True)
        # Export this chart
        png_bytes = figure_to_png_bytes(fig)
        if png_bytes:
            st.download_button(
                "⬇ Download Chart (PNG)",
                data=png_bytes,
                file_name=f"{chart_type.lower().replace(' ', '_')}.png",
                mime="image/png",
            )


# ===========================================================================
# Page 4 — Insights & Summary
# ===========================================================================

def page_insights():
    section_header("💡 Insights & Summary", "Auto-generated analysis and key findings")

    df = _active_df()
    if df is None:
        no_data_warning()
        return

    num_cols = get_numeric_columns(df)
    cat_cols = get_categorical_columns(df)
    date_cols = get_date_columns(df)

    # Value column picker
    value_col = None
    if num_cols:
        value_col = st.selectbox("Primary value column for analysis", num_cols, key="ins_val_col")

    kpis = compute_kpis(df, value_col)
    render_kpi_row(kpis)

    st.divider()

    # Natural language insights
    st.markdown("### 📝 Auto-Generated Insights")
    insights = generate_insights(df, value_col)
    for ins in insights:
        st.markdown(f"- {ins}")

    st.divider()

    # Trend analysis
    if date_cols and value_col:
        st.markdown("### 📅 Trend Analysis")
        freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME", "Quarterly": "QE"}
        freq_label = st.radio("Aggregation", list(freq_map.keys()), horizontal=True, key="ins_freq")
        trend = trend_analysis(df, date_cols[0], value_col, freq=freq_map[freq_label])
        if not trend.empty:
            fig = line_chart(trend, date_cols[0], value_col,
                             title=f"{freq_label} trend of {value_col}")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Category comparison
    if cat_cols and value_col:
        st.markdown("### 📊 Category Comparison")
        cat_choice = st.selectbox("Group by", cat_cols, key="ins_cat_choice")
        comp = category_comparison(df, cat_choice, value_col)
        if not comp.empty:
            fig = bar_chart(
                comp.head(15), cat_choice, "Sum",
                title=f"{value_col} summary by {cat_choice}",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(comp, use_container_width=True)

    st.divider()

    # Outlier highlighting
    if value_col:
        st.markdown("### 🔴 Outlier Analysis")
        outlier_mask = flag_outliers(df, value_col)
        n_outliers = outlier_mask.sum()
        st.metric("Outlier rows detected", int(n_outliers), help="Using IQR × 1.5 method")
        if n_outliers > 0:
            fig = histogram_chart(df, value_col, title=f"Distribution of {value_col} (outliers in red)")
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("View outlier rows"):
                st.dataframe(df[outlier_mask], use_container_width=True)

    st.divider()

    # Correlation matrix
    st.markdown("### 🔗 Correlation Matrix")
    fig = heatmap_chart(df, title="Pearson Correlation Heatmap")
    st.plotly_chart(fig, use_container_width=True)


# ===========================================================================
# Page 5 — Download / Export
# ===========================================================================

def page_export():
    section_header("⬇ Download / Export", "Download filtered data and individual charts")

    df = _active_df()
    if df is None:
        no_data_warning()
        return

    st.markdown(f"Exporting **{len(df):,} rows** × **{df.shape[1]} columns** (current filters applied).")

    st.divider()
    st.markdown("### 📋 Data Exports")
    col1, col2 = st.columns(2)
    with col1:
        csv_bytes = df_to_csv_bytes(df)
        st.download_button(
            label="⬇ Download as CSV",
            data=csv_bytes,
            file_name="filtered_data.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col2:
        xlsx_bytes = df_to_excel_bytes(df)
        st.download_button(
            label="⬇ Download as Excel",
            data=xlsx_bytes,
            file_name="filtered_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.divider()
    st.markdown("### 📊 Chart Exports")
    st.caption("Generate and download any chart as a PNG image.")

    num_cols = get_numeric_columns(df)
    cat_cols = get_categorical_columns(df)
    date_cols = get_date_columns(df)

    chart_choice = st.selectbox(
        "Chart to export",
        ["Top-N Bar", "Pie Chart", "Correlation Heatmap", "Line Chart / Trend"],
        key="export_chart_choice",
    )

    export_fig = None

    if chart_choice == "Top-N Bar" and cat_cols and num_cols:
        c1, c2 = st.columns(2)
        with c1:
            g = st.selectbox("Group by", cat_cols, key="exp_topn_g")
        with c2:
            v = st.selectbox("Value", num_cols, key="exp_topn_v")
        n = st.slider("Top N", 3, 30, 10, key="exp_topn_n")
        export_fig = top_n_bar(df, g, v, n=n, title=f"Top {n} {g} by {v}")

    elif chart_choice == "Pie Chart" and cat_cols and num_cols:
        c1, c2 = st.columns(2)
        with c1:
            names = st.selectbox("Category", cat_cols, key="exp_pie_n")
        with c2:
            vals = st.selectbox("Values", num_cols, key="exp_pie_v")
        agg = df.groupby(names)[vals].sum().reset_index()
        export_fig = pie_chart(agg, names, vals, title=f"{vals} by {names}")

    elif chart_choice == "Correlation Heatmap":
        export_fig = heatmap_chart(df)

    elif chart_choice == "Line Chart / Trend" and date_cols and num_cols:
        c1, c2 = st.columns(2)
        with c1:
            dc = st.selectbox("Date column", date_cols, key="exp_line_dc")
        with c2:
            vc = st.selectbox("Value column", num_cols, key="exp_line_vc")
        from insights import trend_analysis as _ta
        trend = _ta(df, dc, vc)
        if not trend.empty:
            export_fig = line_chart(trend, dc, vc, title=f"{vc} over time")

    if export_fig:
        st.plotly_chart(export_fig, use_container_width=True)
        png_bytes = figure_to_png_bytes(export_fig)
        if png_bytes:
            st.download_button(
                "⬇ Download Chart (PNG)",
                data=png_bytes,
                file_name=f"{chart_choice.lower().replace(' ', '_')}.png",
                mime="image/png",
                type="primary",
            )
        else:
            st.warning("PNG export requires the 'kaleido' package. Run: pip install kaleido")


# ===========================================================================
# Page 6 — Debug / Data Preview
# ===========================================================================

def page_debug():
    section_header("🛠 Debug / Data Preview", "Inspect raw and processed data")

    df_raw = st.session_state.get("df_raw")
    df_clean = st.session_state.get("df_clean")
    df_filtered = st.session_state.get("df_filtered")

    if df_raw is None:
        no_data_warning()
        return

    active = df_filtered or df_clean or df_raw

    with st.expander("📋 Active DataFrame — Head (20 rows)", expanded=True):
        st.dataframe(active.head(20), use_container_width=True)

    with st.expander("🔢 Data Types", expanded=False):
        dtypes_df = pd.DataFrame({
            "Column": active.dtypes.index,
            "Dtype": active.dtypes.values.astype(str),
        })
        st.dataframe(dtypes_df, use_container_width=True)

    with st.expander("📐 Shape & Memory", expanded=False):
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", f"{active.shape[0]:,}")
        col2.metric("Columns", active.shape[1])
        col3.metric("Memory (MB)", f"{memory_usage_mb(active):.3f}")

    with st.expander("❓ Missing Values (%)", expanded=False):
        ms = missing_summary(active)
        st.dataframe(ms, use_container_width=True)

    with st.expander("📊 Descriptive Statistics", expanded=False):
        st.dataframe(active.describe(include="all").T, use_container_width=True)

    with st.expander("🗄 Session State Keys", expanded=False):
        safe_state = {
            k: (f"DataFrame({v.shape})" if isinstance(v, pd.DataFrame) else str(v))
            for k, v in st.session_state.items()
        }
        st.json(safe_state)


# ===========================================================================
# Navigation setup
# ===========================================================================

pages = {
    "🏠 Home": page_home,
    "📂 Upload & Cleaning": page_upload,
    "📈 Visualizations": page_visualizations,
    "💡 Insights": page_insights,
    "⬇ Export": page_export,
    "🛠 Debug": page_debug,
}

render_sidebar()

# Tab-based navigation (compatible with all Streamlit versions)
tab_labels = list(pages.keys())
tabs = st.tabs(tab_labels)
for tab, (label, page_fn) in zip(tabs, pages.items()):
    with tab:
        page_fn()
