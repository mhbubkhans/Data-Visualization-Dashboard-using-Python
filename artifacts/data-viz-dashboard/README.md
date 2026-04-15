# Data Visualization Dashboard

A professional, interactive, multi-page data visualization dashboard built with Streamlit and Plotly. Upload any CSV or Excel file and instantly explore your data with 8+ chart types, auto-generated insights, smart cleaning tools, and one-click exports.

## Features

- **File Upload** — CSV and Excel (.xlsx/.xls) with validation and progress feedback
- **Sample Dataset** — 1,200-row generic dataset auto-loaded with one click
- **Data Cleaning** — Missing value handling (drop/fill mean/median/mode), deduplication, date parsing, numeric conversion, IQR outlier removal
- **Sidebar Filters** — Date range, multi-select categories, numeric sliders, text search — all persistent via session state
- **KPI Cards** — Row count, totals, averages, max/min, missing cells, duplicates
- **8+ Interactive Charts** — Line, Bar, Pie, Scatter, Histogram, Box Plot, Area Chart, Correlation Heatmap, Top-N Bar
- **Auto Insights** — Natural-language summary, trend analysis, category comparison, outlier detection
- **Export** — Filtered data as CSV or Excel; individual charts as PNG images
- **Debug Panel** — df.head(), dtypes, shape, missing %, memory usage, session state inspector

## Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| Streamlit | ≥1.30 | Web app framework |
| Pandas | ≥2.0 | Data manipulation |
| Plotly | ≥5.18 | Interactive charts |
| NumPy | ≥1.26 | Numerical operations |
| OpenPyXL | ≥3.1 | Excel write support |
| xlrd | ≥2.0 | Legacy Excel read |
| kaleido | ≥0.2 | Chart PNG export |

## Project Structure

```
data-viz-dashboard/
├── app.py                 # Main entry point — navigation & page rendering
├── data_processing.py     # Loading, cleaning, filtering, validation
├── visualizations.py      # Plotly chart factories (reusable functions)
├── insights.py            # KPI logic, trend analysis, auto insights
├── utils.py               # Export helpers, session state, UI components
├── sample_data.csv        # 1,200-row generic demo dataset
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── .streamlit/
│   └── config.toml        # Server port, theme, and browser settings
└── report/
    └── PROJECT_REPORT.md  # Full academic project report
```

## Installation

```bash
# 1. Clone or download this project
cd data-viz-dashboard

# 2. (Optional) create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py --server.port 5000
```

Open your browser at **http://localhost:5000** (or the URL printed in the terminal).

## Quick Start

1. Open the app in your browser.
2. Click **Load Sample Dataset** on the Home page to explore immediately.
3. Or go to **Upload & Cleaning** to upload your own CSV/Excel file.
4. Use the **sidebar filters** to narrow down the data.
5. Navigate to **Visualizations** to build interactive charts.
6. Visit **Insights** for auto-generated analysis.
7. Use **Export** to download filtered data or chart images.

## Extending the Dashboard

### Add a new chart type

In `visualizations.py`, define a new function following the pattern:

```python
def my_chart(df, x_col, y_col, title="My Chart"):
    fig = px.some_chart(df, x=x_col, y=y_col)
    return _base_layout(fig, title)
```

Then register it in `CHART_REGISTRY`:

```python
CHART_REGISTRY["My Chart"] = my_chart
```

It will automatically appear in the chart type selector on the Visualizations page.

### Add a new cleaning step

In `data_processing.py`, add a new function and call it inside `apply_cleaning_steps()`.

### Change the theme

Edit `.streamlit/config.toml` — change `primaryColor`, `backgroundColor`, `textColor`, etc.

## Screenshots

*Add screenshots of each page here after deployment.*

| Page | Description |
|------|-------------|
| Home / Overview | KPI cards + quick charts |
| Upload & Cleaning | File upload + cleaning options |
| Visualizations | Chart builder |
| Insights | Auto insights + trend analysis |
| Export | Download filtered data + charts |
| Debug | Raw data inspection |
