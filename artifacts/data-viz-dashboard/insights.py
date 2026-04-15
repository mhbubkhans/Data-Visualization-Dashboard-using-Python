"""
insights.py
-----------
Auto-generated KPIs, natural-language insights, and trend analysis.
"""

from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# KPI calculation
# ---------------------------------------------------------------------------

def compute_kpis(df: pd.DataFrame, value_col: Optional[str] = None) -> dict:
    """
    Compute key performance indicators from the DataFrame.
    Returns a dict of {label: value} pairs.
    """
    kpis = {}
    kpis["Total Rows"] = len(df)
    kpis["Total Columns"] = len(df.columns)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if value_col and value_col in df.columns and pd.api.types.is_numeric_dtype(df[value_col]):
        col = df[value_col].dropna()
        kpis["Total"] = f"{col.sum():,.2f}"
        kpis["Average"] = f"{col.mean():,.2f}"
        kpis["Max"] = f"{col.max():,.2f}"
        kpis["Min"] = f"{col.min():,.2f}"
        kpis["Std Dev"] = f"{col.std():,.2f}"
    elif numeric_cols:
        first = numeric_cols[0]
        col = df[first].dropna()
        kpis[f"Sum ({first})"] = f"{col.sum():,.2f}"
        kpis[f"Mean ({first})"] = f"{col.mean():,.2f}"

    missing_total = df.isnull().sum().sum()
    kpis["Missing Cells"] = int(missing_total)
    kpis["Duplicate Rows"] = int(df.duplicated().sum())

    return kpis


# ---------------------------------------------------------------------------
# Trend analysis
# ---------------------------------------------------------------------------

def trend_analysis(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    freq: str = "ME",
) -> pd.DataFrame:
    """
    Aggregate value_col by date_col at the given frequency.
    Returns a DataFrame with columns: [date_col, value_col, rolling_avg].
    freq: pandas offset alias (e.g. 'ME' monthly end, 'W' weekly, 'D' daily).
    """
    try:
        tmp = df[[date_col, value_col]].copy()
        tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
        tmp = tmp.dropna()
        tmp = tmp.set_index(date_col).resample(freq)[value_col].sum().reset_index()
        tmp["rolling_avg"] = tmp[value_col].rolling(3, min_periods=1).mean()
        return tmp
    except Exception:
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Category comparison
# ---------------------------------------------------------------------------

def category_comparison(
    df: pd.DataFrame,
    cat_col: str,
    value_col: str,
) -> pd.DataFrame:
    """
    Group by cat_col and compute summary stats for value_col.
    Returns a DataFrame sorted by sum descending.
    """
    try:
        grouped = df.groupby(cat_col)[value_col].agg(
            Count="count",
            Sum="sum",
            Mean="mean",
            Median="median",
            Std="std",
        ).reset_index()
        return grouped.sort_values("Sum", ascending=False)
    except Exception:
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Natural-language summary
# ---------------------------------------------------------------------------

def generate_insights(df: pd.DataFrame, value_col: Optional[str] = None) -> list:
    """
    Produce a list of natural-language insight strings about the dataset.
    """
    insights = []
    rows, cols = df.shape
    insights.append(f"The dataset contains **{rows:,} rows** and **{cols} columns**.")

    # Missing data
    missing_pct = df.isnull().mean().mean() * 100
    if missing_pct == 0:
        insights.append("The data is **complete** — no missing values detected.")
    elif missing_pct < 5:
        insights.append(f"Overall missing data is low at **{missing_pct:.1f}%** of all cells.")
    else:
        worst_col = df.isnull().mean().idxmax()
        worst_pct = df.isnull().mean().max() * 100
        insights.append(
            f"Missing data averages **{missing_pct:.1f}%**. "
            f"Column **'{worst_col}'** has the highest rate at **{worst_pct:.0f}%**."
        )

    # Duplicates
    dups = df.duplicated().sum()
    if dups:
        insights.append(f"There are **{dups:,} duplicate rows** in the dataset.")
    else:
        insights.append("No duplicate rows detected.")

    # Numeric column insights
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if value_col and value_col in numeric_cols:
        col = df[value_col].dropna()
        total = col.sum()
        mean = col.mean()
        skew = col.skew()
        insights.append(
            f"**{value_col}** sums to **{total:,.2f}** with a mean of **{mean:,.2f}**."
        )
        if abs(skew) > 1:
            direction = "right (positively)" if skew > 0 else "left (negatively)"
            insights.append(
                f"The distribution of **{value_col}** is skewed **{direction}** (skewness = {skew:.2f})."
            )
        outlier_fence = mean + 3 * col.std()
        n_outliers = (col > outlier_fence).sum()
        if n_outliers:
            insights.append(
                f"**{n_outliers}** potential high-value outliers detected in **{value_col}** (beyond 3σ)."
            )

    # Categorical column insights
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        most_diverse = max(cat_cols, key=lambda c: df[c].nunique())
        insights.append(
            f"Column **'{most_diverse}'** has the highest cardinality with "
            f"**{df[most_diverse].nunique()}** unique values."
        )
        for col in cat_cols[:3]:
            top_val = df[col].mode().iloc[0] if not df[col].mode().empty else "N/A"
            top_pct = (df[col] == top_val).mean() * 100
            insights.append(
                f"The most common **{col}** is **'{top_val}'**, appearing in {top_pct:.1f}% of rows."
            )

    # Date insights
    date_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    if date_cols:
        dc = date_cols[0]
        min_d, max_d = df[dc].min(), df[dc].max()
        span = (max_d - min_d).days
        insights.append(
            f"The date column **'{dc}'** spans from **{min_d.date()}** to **{max_d.date()}** ({span} days)."
        )

    return insights


# ---------------------------------------------------------------------------
# Outlier detection
# ---------------------------------------------------------------------------

def flag_outliers(df: pd.DataFrame, col: str) -> pd.Series:
    """
    Return a boolean Series marking outliers in col using the IQR method.
    True  = outlier, False = normal.
    """
    if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
        return pd.Series([False] * len(df), index=df.index)
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    return (df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)
