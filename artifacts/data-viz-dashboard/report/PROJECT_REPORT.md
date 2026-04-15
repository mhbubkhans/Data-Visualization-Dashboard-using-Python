# Data Visualization Dashboard using Python
## Full Project Report

---

## Title Page

| | |
|--|--|
| **Project Title** | Data Visualization Dashboard using Python |
| **Technology** | Python, Streamlit, Pandas, Plotly, NumPy, OpenPyXL |
| **Type** | Major Semester Project |
| **Date** | 2024–2025 |

---

## Abstract

This project presents a complete, production-quality Data Visualization Dashboard built entirely in Python using Streamlit and Plotly. The dashboard is a generic analytics tool that works with any user-uploaded CSV or Excel file and provides immediate, interactive visual exploration of that data. Key capabilities include intelligent data cleaning, persistent sidebar filtering, 8+ Plotly chart types with dynamic column pickers, auto-generated natural-language insights, KPI summary cards, outlier detection, trend analysis, and one-click export of both filtered data (CSV/Excel) and individual charts (PNG). The system is modular, well-documented, and beginner-friendly while remaining polished enough for a professional or academic setting.

---

## 1. Problem Statement

Organizations and students frequently deal with data stored in flat files (CSV, Excel) but lack quick, accessible tools to visualize and analyze that data without installing complex BI platforms or writing custom code for every dataset. Existing solutions either require deep technical knowledge or are locked to specific data schemas.

**This project solves that problem** by providing a plug-and-play dashboard that:
- Works with **any** structured CSV or Excel file
- Requires no programming knowledge to use
- Delivers professional-grade visualizations and insights instantly
- Runs fully in the browser via Streamlit

---

## 2. Objectives

1. Build a multi-page interactive dashboard using Python and Streamlit.
2. Support CSV and Excel file formats with robust error handling.
3. Implement a complete data cleaning pipeline (missing values, duplicates, outliers, date parsing, numeric conversion).
4. Provide sidebar filters (date range, category multi-select, numeric sliders, text search) that persist across page navigation.
5. Deliver 8+ distinct Plotly chart types with user-controlled column mapping.
6. Auto-generate KPI cards and natural-language data insights.
7. Enable one-click export of filtered data (CSV, Excel) and charts (PNG).
8. Provide a debug panel for data inspection and profiling.

---

## 3. System Architecture

```
┌───────────────────────────────────────────────────────────┐
│                    Browser (User)                         │
└───────────────────────────┬───────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼───────────────────────────────┐
│              Streamlit Web Server (app.py)                 │
│                                                            │
│   ┌─────────────────────────────────────────────────┐     │
│   │  Navigation Layer (st.tabs)                     │     │
│   │  Home │ Upload │ Visualizations │ Insights       │     │
│   │  Export │ Debug                                  │     │
│   └──────────────────┬──────────────────────────────┘     │
│                      │                                     │
│   ┌──────────────────▼──────────────────────────────┐     │
│   │  Session State (st.session_state)               │     │
│   │  df_raw │ df_clean │ df_filtered │ filters      │     │
│   └──────┬────────────────────────┬─────────────────┘     │
│          │                        │                        │
│   ┌──────▼──────┐    ┌────────────▼────────────┐          │
│   │ data_       │    │ visualizations.py       │          │
│   │ processing  │    │ 8+ Plotly chart funcs   │          │
│   │ .py         │    └────────────┬────────────┘          │
│   │ load/clean/ │                 │                        │
│   │ filter      │    ┌────────────▼────────────┐          │
│   └──────┬──────┘    │ insights.py             │          │
│          │           │ KPIs, trends, NL text   │          │
│   ┌──────▼──────┐    └─────────────────────────┘          │
│   │ utils.py    │                                          │
│   │ export /    │    ┌─────────────────────────┐          │
│   │ session /   │    │ sample_data.csv         │          │
│   │ UI helpers  │    │ 1,200-row demo dataset  │          │
│   └─────────────┘    └─────────────────────────┘          │
└───────────────────────────────────────────────────────────┘
```

Data flows left to right:
1. User uploads a file → `data_processing.py` validates and loads it → stored in `st.session_state`
2. User applies cleaning → `data_processing.py` transforms the raw df → stored as `df_clean`
3. Sidebar filters run → `apply_filters()` produces `df_filtered` used by all pages
4. Each page reads `df_filtered` and passes it to `visualizations.py` or `insights.py`

---

## 4. Tools & Technologies

| Tool | Version | Role |
|------|---------|------|
| Python | 3.11 | Core language |
| Streamlit | ≥1.30 | Web UI framework |
| Pandas | ≥2.0 | Data loading, cleaning, filtering |
| Plotly Express | ≥5.18 | Interactive chart generation |
| Plotly Graph Objects | ≥5.18 | Low-level chart customization |
| NumPy | ≥1.26 | Numerical computation |
| OpenPyXL | ≥3.1 | Excel file writing |
| xlrd | ≥2.0 | Legacy .xls reading |
| kaleido | ≥0.2 | Chart-to-PNG export |

---

## 5. Module Description

### 5.1 `app.py` — Main Entry Point
Initialises the Streamlit page config, renders the persistent sidebar (branding + filters), and coordinates the six-page `st.tabs` navigation. Acts as the controller layer — it imports all other modules and calls their functions but contains no business logic of its own.

### 5.2 `data_processing.py` — Data Pipeline
**Loading:** `load_file()` dispatches to `load_csv()` or `load_excel()` based on file extension. Both are decorated with `@st.cache_data` to avoid re-reading files on every rerun.

**Validation:** `validate_dataframe()` checks for empty DataFrames and columns with >50% missing values.

**Cleaning:** Six atomic cleaning functions (`drop_missing_rows`, `fill_missing_mean`, `fill_missing_median`, `fill_missing_mode`, `remove_duplicates`, `remove_outliers_iqr`) are composed by `apply_cleaning_steps()` based on user selections.

**Filtering:** `apply_filters()` accepts a DataFrame and filter parameters and returns the filtered subset.

### 5.3 `visualizations.py` — Chart Factory
Provides 9 reusable chart functions, each accepting a DataFrame and returning a Plotly `Figure` object. A `_base_layout()` helper applies a consistent theme across all charts. All chart functions are registered in `CHART_REGISTRY` (a dict mapping display names to functions) which drives the chart-type selector UI.

### 5.4 `insights.py` — Intelligence Layer
- `compute_kpis()` — Computes totals, averages, min/max, missing cell count, duplicate count.
- `trend_analysis()` — Resamples a numeric column by a date column at any pandas offset frequency (daily, weekly, monthly, quarterly). Computes a 3-period rolling average.
- `category_comparison()` — Groups by a categorical column and computes summary stats for a numeric column.
- `generate_insights()` — Produces a list of natural-language observations covering data shape, missing data, duplicates, value distribution, skewness, cardinality, and date ranges.
- `flag_outliers()` — Returns a boolean mask identifying IQR outliers.

### 5.5 `utils.py` — Helpers
- Session state initialisation and reset functions.
- `df_to_csv_bytes()` and `df_to_excel_bytes()` for `st.download_button` compatibility.
- `figure_to_png_bytes()` wrapping Plotly's kaleido export.
- `kpi_card()` and `render_kpi_row()` for consistent KPI display.
- `section_header()`, `info_box()`, `no_data_warning()` for DRY UI rendering.

---

## 6. Implementation Details

### Session State Strategy
All mutable application state (loaded DataFrames, filter parameters, cleaning log) is stored in `st.session_state`. The hierarchy is: `df_raw` → `df_clean` → `df_filtered`. Each downstream stage is re-computed only when the user explicitly triggers it (Apply Cleaning button, or any sidebar filter change).

### Caching Strategy
`@st.cache_data` is applied to I/O-bound functions (`load_csv`, `load_excel`, `load_sample_data`). This prevents re-reading files on every Streamlit rerun. The cache is keyed by function arguments (file bytes hash + filename), so different uploads get separate cache entries.

### Error Handling
- File loading is wrapped in `try/except`; the error message is returned as a plain string and displayed via `st.error()`. The app never crashes on a bad file.
- Chart functions guard against empty or insufficient data and return informative placeholder figures.
- All `pd.to_datetime()` and `pd.to_numeric()` calls use `errors="coerce"` to handle partial or mixed-format columns gracefully.

### Responsive Layout
Streamlit's `st.columns()` grid is used throughout to create responsive multi-column layouts. The sidebar provides persistent filter controls without re-rendering the main content area.

---

## 7. Module Interactions (Data Flow)

```
User Action → app.py
    ↓
    File upload or sample button
    ↓
    data_processing.load_file()
    ↓
    st.session_state["df_raw"]
    ↓
    data_processing.apply_cleaning_steps()  ← user chooses options
    ↓
    st.session_state["df_clean"]
    ↓
    data_processing.apply_filters()  ← sidebar updates
    ↓
    st.session_state["df_filtered"]
    ↓
    ┌──────────────────────────────────────────────┐
    │  Visualizations page → visualizations.py    │
    │  Insights page → insights.py                │
    │  Export page → utils.py (export helpers)    │
    │  Debug page → raw df.describe() / head()    │
    └──────────────────────────────────────────────┘
```

---

## 8. Screenshots

*[Screenshots to be added after deployment]*

| Screenshot | Description |
|------------|-------------|
| `home.png` | Home page with KPI cards and quick charts |
| `upload.png` | Upload & Cleaning page |
| `visualizations.png` | Scatter plot with color encoding |
| `insights.png` | Auto-generated insights and trend chart |
| `export.png` | Export page with download buttons |
| `debug.png` | Debug panel showing dtypes and stats |

---

## 9. Testing

The application was tested with the following scenarios:

| Test Case | Expected Outcome | Result |
|-----------|-----------------|--------|
| Upload valid CSV (1,200 rows) | Data loaded, shape shown | Pass |
| Upload Excel (.xlsx) | Data loaded correctly | Pass |
| Upload invalid file format | User-friendly error shown | Pass |
| Load sample data button | 1,200-row dataset appears | Pass |
| Apply "Drop rows" cleaning | Rows with NaN removed, count updated | Pass |
| Apply "Fill with Mean" | Numeric NaN filled, no errors | Pass |
| Remove duplicates | Duplicate count in KPIs drops to 0 | Pass |
| Date range filter | Only rows within range shown | Pass |
| Category multi-select filter | Only selected categories shown | Pass |
| Numeric slider filter | Min/max range applied correctly | Pass |
| Text search filter | Matching rows returned | Pass |
| Reset Filters button | All filters cleared, data restored | Pass |
| Line chart with date X | Chart renders with time axis | Pass |
| Heatmap with < 2 numeric cols | Placeholder message shown | Pass |
| Export CSV download | Valid CSV file downloads | Pass |
| Export Excel download | Valid .xlsx file downloads | Pass |
| PNG chart export | PNG image file downloads | Pass |
| Empty dataset upload | Error message shown, no crash | Pass |

---

## 10. Conclusion

This project successfully delivers a complete, professional-grade data visualization dashboard using exclusively Python open-source libraries. The modular architecture ensures maintainability, and the clean separation between data processing, visualization, insights, and UI utilities makes it straightforward to extend. The application handles edge cases gracefully, never crashes on bad input, and provides a polished user experience suitable for both classroom demonstrations and real analytical use.

---

## 11. Future Scope

1. **Machine Learning Integration** — Add a page for clustering (K-Means), regression, or anomaly detection using scikit-learn.
2. **Natural Language Querying** — Allow users to ask questions about the data in plain English (using an LLM API).
3. **Database Connectivity** — Support direct connections to PostgreSQL, MySQL, or SQLite.
4. **Real-time Data** — Stream live data via WebSocket or polling for IoT / monitoring use cases.
5. **Multi-file Merging** — Allow users to upload and join multiple files before analyzing.
6. **Report Generation** — Auto-generate a PDF report summarizing all KPIs and charts.
7. **User Authentication** — Add login / role-based access for shared deployments.
8. **Custom Dashboard Builder** — Let users drag and drop charts into a custom layout that persists across sessions.

---

## 12. Appendix — Key Code Snippets

### A. Cached File Loading

```python
@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], str]:
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
        return df, ""
    except Exception as exc:
        return None, f"Could not read CSV '{filename}': {exc}"
```

### B. IQR Outlier Removal

```python
def remove_outliers_iqr(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include=[np.number]).columns:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        df = df[(df[col] >= q1 - 1.5 * iqr) & (df[col] <= q3 + 1.5 * iqr)]
    return df
```

### C. Chart Factory Pattern

```python
def bar_chart(df, x_col, y_col, color_col=None, orientation="v", title="Bar Chart"):
    fig = px.bar(df, x=x_col, y=y_col, color=color_col,
                 color_discrete_sequence=_PALETTE)
    return _base_layout(fig, title)

CHART_REGISTRY = {
    "Bar Chart": bar_chart,
    "Line Chart": line_chart,
    ...
}
```

### D. Filter Application

```python
def apply_filters(df, date_col, date_range, cat_filters, num_filters, text_search):
    filtered = df.copy()
    if date_col and date_range:
        start, end = date_range
        filtered = filtered[(filtered[date_col] >= pd.Timestamp(start)) &
                            (filtered[date_col] <= pd.Timestamp(end))]
    for col, selected in cat_filters.items():
        if selected:
            filtered = filtered[filtered[col].isin(selected)]
    for col, (lo, hi) in num_filters.items():
        filtered = filtered[(filtered[col] >= lo) & (filtered[col] <= hi)]
    if text_search:
        query = text_search.lower()
        mask = pd.Series([False] * len(filtered), index=filtered.index)
        for col in filtered.select_dtypes(include="object").columns:
            mask |= filtered[col].astype(str).str.lower().str.contains(query, na=False)
        filtered = filtered[mask]
    return filtered
```

### E. Natural Language Insight Generation

```python
def generate_insights(df, value_col=None):
    insights = []
    missing_pct = df.isnull().mean().mean() * 100
    if missing_pct == 0:
        insights.append("The data is **complete** — no missing values detected.")
    else:
        insights.append(f"Overall missing data is **{missing_pct:.1f}%** of all cells.")
    # ... more rules
    return insights
```

---

*End of Project Report*
