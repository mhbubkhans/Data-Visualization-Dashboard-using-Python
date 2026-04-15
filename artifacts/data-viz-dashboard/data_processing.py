"""
data_processing.py
------------------
All data loading, cleaning, validation, and transformation logic.
"""

import io
import re
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], str]:
    """Load a CSV file from raw bytes and return (DataFrame, error_message)."""
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
        return df, ""
    except Exception as exc:
        return None, f"Could not read CSV '{filename}': {exc}"


@st.cache_data(show_spinner=False)
def load_excel(file_bytes: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], str]:
    """Load an Excel file from raw bytes and return (DataFrame, error_message)."""
    try:
        df = pd.read_excel(io.BytesIO(file_bytes))
        return df, ""
    except Exception as exc:
        return None, f"Could not read Excel '{filename}': {exc}"


def load_file(uploaded_file) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Dispatch to the appropriate loader based on file extension.
    Returns (DataFrame, error_message).
    """
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    if name.endswith(".csv"):
        return load_csv(raw, uploaded_file.name)
    elif name.endswith((".xlsx", ".xls")):
        return load_excel(raw, uploaded_file.name)
    else:
        return None, f"Unsupported file type: '{uploaded_file.name}'. Please upload CSV or Excel."


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_sample_data() -> pd.DataFrame:
    """Load the bundled sample_data.csv shipped with the project."""
    try:
        return pd.read_csv("sample_data.csv")
    except FileNotFoundError:
        return _generate_fallback_sample()


def _generate_fallback_sample() -> pd.DataFrame:
    """Generate a synthetic dataset in memory if sample_data.csv is missing."""
    rng = np.random.default_rng(42)
    n = 1000
    dates = pd.date_range("2022-01-01", periods=n, freq="D")
    categories = rng.choice(["Electronics", "Clothing", "Home & Garden", "Sports", "Books"], n)
    sub_categories = {
        "Electronics": ["Phones", "Laptops", "Tablets", "Accessories"],
        "Clothing": ["Men", "Women", "Kids", "Footwear"],
        "Home & Garden": ["Furniture", "Decor", "Kitchen", "Tools"],
        "Sports": ["Fitness", "Outdoor", "Team Sports", "Water Sports"],
        "Books": ["Fiction", "Non-Fiction", "Science", "History"],
    }
    subs = [rng.choice(sub_categories[c]) for c in categories]
    regions = rng.choice(["North", "South", "East", "West", "Central"], n)
    customer_types = rng.choice(["Retail", "Wholesale", "Online"], n)
    values = np.round(rng.uniform(10, 5000, n), 2)
    quantities = rng.integers(1, 50, n)
    return pd.DataFrame({
        "Date": dates,
        "Category": categories,
        "Sub_Category": subs,
        "Region": regions,
        "Customer_Type": customer_types,
        "Value": values,
        "Quantity": quantities,
        "Revenue": np.round(values * quantities * rng.uniform(0.8, 1.2, n), 2),
    })


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, list]:
    """
    Basic sanity checks on a freshly loaded DataFrame.
    Returns (is_valid, list_of_warnings).
    """
    warnings = []
    if df.empty:
        return False, ["The dataset is empty — please upload a file with at least one row."]
    if len(df.columns) < 2:
        warnings.append("The dataset has fewer than 2 columns. Some features may not work.")
    missing_pct = df.isnull().mean() * 100
    high_missing = missing_pct[missing_pct > 50]
    if not high_missing.empty:
        for col, pct in high_missing.items():
            warnings.append(f"Column '{col}' has {pct:.0f}% missing values.")
    return True, warnings


# ---------------------------------------------------------------------------
# Cleaning operations
# ---------------------------------------------------------------------------

def drop_missing_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop all rows with any missing value."""
    return df.dropna()


def fill_missing_mean(df: pd.DataFrame) -> pd.DataFrame:
    """Fill numeric NaNs with column mean; fill object NaNs with mode."""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].mean())
        else:
            mode = df[col].mode()
            if not mode.empty:
                df[col] = df[col].fillna(mode[0])
    return df


def fill_missing_median(df: pd.DataFrame) -> pd.DataFrame:
    """Fill numeric NaNs with column median; fill object NaNs with mode."""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        else:
            mode = df[col].mode()
            if not mode.empty:
                df[col] = df[col].fillna(mode[0])
    return df


def fill_missing_mode(df: pd.DataFrame) -> pd.DataFrame:
    """Fill all NaNs with column mode (works for numeric and categorical)."""
    df = df.copy()
    for col in df.columns:
        mode = df[col].mode()
        if not mode.empty:
            df[col] = df[col].fillna(mode[0])
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows (keep first occurrence)."""
    return df.drop_duplicates()


def auto_parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Attempt to convert columns whose names suggest they are dates."""
    df = df.copy()
    date_patterns = re.compile(r"date|time|dt|year|month|day", re.I)
    for col in df.select_dtypes(include="object").columns:
        if date_patterns.search(col):
            try:
                df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors="raise")
            except Exception:
                pass  # Leave as-is if conversion fails
    return df


def convert_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Try to coerce object columns to numeric where possible."""
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().sum() / max(len(df), 1) > 0.6:
            df[col] = converted
    return df


def remove_outliers_iqr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows where any numeric column value falls outside
    1.5 * IQR from the quartiles.
    """
    df = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        df = df[(df[col] >= lower) & (df[col] <= upper)]
    return df


def apply_cleaning_steps(
    df: pd.DataFrame,
    missing_strategy: str = "none",
    deduplicate: bool = False,
    parse_dates: bool = False,
    convert_nums: bool = False,
    remove_outliers: bool = False,
) -> Tuple[pd.DataFrame, list]:
    """
    Apply a series of cleaning steps based on user-selected options.
    Returns (cleaned_df, list_of_applied_steps).
    """
    steps_applied = []
    original_rows = len(df)

    if parse_dates:
        df = auto_parse_dates(df)
        steps_applied.append("Auto date parsing applied.")

    if convert_nums:
        df = convert_numeric(df)
        steps_applied.append("Numeric conversion applied.")

    if missing_strategy == "Drop rows":
        df = drop_missing_rows(df)
        steps_applied.append(f"Dropped rows with missing values ({original_rows - len(df)} rows removed).")
    elif missing_strategy == "Fill with Mean":
        df = fill_missing_mean(df)
        steps_applied.append("Missing values filled with column mean / mode.")
    elif missing_strategy == "Fill with Median":
        df = fill_missing_median(df)
        steps_applied.append("Missing values filled with column median / mode.")
    elif missing_strategy == "Fill with Mode":
        df = fill_missing_mode(df)
        steps_applied.append("Missing values filled with column mode.")

    if deduplicate:
        before = len(df)
        df = remove_duplicates(df)
        steps_applied.append(f"Removed duplicates ({before - len(df)} rows removed).")

    if remove_outliers:
        before = len(df)
        df = remove_outliers_iqr(df)
        steps_applied.append(f"Removed outliers via IQR ({before - len(df)} rows removed).")

    return df, steps_applied


# ---------------------------------------------------------------------------
# Filtering helpers
# ---------------------------------------------------------------------------

def get_date_columns(df: pd.DataFrame) -> list:
    """Return column names with datetime dtype."""
    return list(df.select_dtypes(include=["datetime", "datetimetz"]).columns)


def get_numeric_columns(df: pd.DataFrame) -> list:
    """Return column names with numeric dtype."""
    return list(df.select_dtypes(include=[np.number]).columns)


def get_categorical_columns(df: pd.DataFrame) -> list:
    """Return column names with object or category dtype."""
    return list(df.select_dtypes(include=["object", "category"]).columns)


def apply_filters(
    df: pd.DataFrame,
    date_col: Optional[str],
    date_range: Optional[Tuple],
    cat_filters: dict,
    num_filters: dict,
    text_search: str,
) -> pd.DataFrame:
    """
    Apply all active sidebar filters to df.

    Parameters
    ----------
    df           : source DataFrame
    date_col     : column to filter by date, or None
    date_range   : (start, end) tuple of date objects, or None
    cat_filters  : {col: [selected_values]}
    num_filters  : {col: (min_val, max_val)}
    text_search  : free-text search string (searches all object columns)
    """
    filtered = df.copy()

    if date_col and date_range and date_col in filtered.columns:
        start, end = date_range
        col = filtered[date_col]
        if pd.api.types.is_datetime64_any_dtype(col):
            start_ts = pd.Timestamp(start)
            end_ts = pd.Timestamp(end)
            filtered = filtered[(col >= start_ts) & (col <= end_ts)]

    for col, selected in cat_filters.items():
        if selected and col in filtered.columns:
            filtered = filtered[filtered[col].isin(selected)]

    for col, (lo, hi) in num_filters.items():
        if col in filtered.columns:
            filtered = filtered[(filtered[col] >= lo) & (filtered[col] <= hi)]

    if text_search:
        query = text_search.lower()
        mask = pd.Series([False] * len(filtered), index=filtered.index)
        for col in filtered.select_dtypes(include="object").columns:
            mask |= filtered[col].astype(str).str.lower().str.contains(query, na=False)
        filtered = filtered[mask]

    return filtered


# ---------------------------------------------------------------------------
# Summary / profile helpers
# ---------------------------------------------------------------------------

def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame summarising missing values per column."""
    total = len(df)
    missing_count = df.isnull().sum()
    missing_pct = (missing_count / total * 100).round(2)
    return pd.DataFrame({
        "Missing Count": missing_count,
        "Missing %": missing_pct,
        "Data Type": df.dtypes.astype(str),
    })


def memory_usage_mb(df: pd.DataFrame) -> float:
    """Return the DataFrame memory usage in megabytes."""
    return df.memory_usage(deep=True).sum() / 1024**2
