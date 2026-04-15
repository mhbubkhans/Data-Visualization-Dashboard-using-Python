"""
visualizations.py
-----------------
Reusable Plotly chart factory functions for the dashboard.
Every function takes a DataFrame and configuration params,
and returns a plotly Figure object.
"""

from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

_PALETTE = px.colors.qualitative.Plotly


def _base_layout(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply a consistent base layout to all figures."""
    fig.update_layout(
        title=dict(text=title, x=0.02, font=dict(size=16)),
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(200,200,200,0.3)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(200,200,200,0.3)")
    return fig


# ---------------------------------------------------------------------------
# 8+ chart types
# ---------------------------------------------------------------------------

def line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: str = "Line Chart",
) -> go.Figure:
    """Time-series or ordered line chart."""
    fig = px.line(
        df, x=x_col, y=y_col, color=color_col,
        color_discrete_sequence=_PALETTE,
    )
    return _base_layout(fig, title)


def bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    orientation: str = "v",
    title: str = "Bar Chart",
) -> go.Figure:
    """Vertical or horizontal bar chart."""
    if orientation == "h":
        fig = px.bar(df, x=y_col, y=x_col, color=color_col,
                     orientation="h", color_discrete_sequence=_PALETTE)
    else:
        fig = px.bar(df, x=x_col, y=y_col, color=color_col,
                     color_discrete_sequence=_PALETTE)
    return _base_layout(fig, title)


def pie_chart(
    df: pd.DataFrame,
    names_col: str,
    values_col: str,
    title: str = "Pie Chart",
) -> go.Figure:
    """Pie / donut chart with a hole for modern look."""
    fig = px.pie(
        df, names=names_col, values=values_col,
        color_discrete_sequence=_PALETTE, hole=0.35,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _base_layout(fig, title)


def scatter_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    title: str = "Scatter Plot",
) -> go.Figure:
    """Scatter plot with optional colour and size encoding."""
    fig = px.scatter(
        df, x=x_col, y=y_col, color=color_col, size=size_col,
        color_discrete_sequence=_PALETTE, opacity=0.7,
        trendline="ols" if color_col is None else None,
    )
    return _base_layout(fig, title)


def histogram_chart(
    df: pd.DataFrame,
    col: str,
    color_col: Optional[str] = None,
    nbins: int = 30,
    title: str = "Histogram",
) -> go.Figure:
    """Distribution histogram with optional color split."""
    fig = px.histogram(
        df, x=col, color=color_col, nbins=nbins,
        color_discrete_sequence=_PALETTE, barmode="overlay",
        marginal="rug",
    )
    return _base_layout(fig, title)


def box_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: str = "Box Plot",
) -> go.Figure:
    """Box-and-whisker plot for distribution comparison."""
    fig = px.box(
        df, x=x_col, y=y_col, color=color_col,
        color_discrete_sequence=_PALETTE, notched=False,
        points="outliers",
    )
    return _base_layout(fig, title)


def area_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: str = "Area Chart",
) -> go.Figure:
    """Stacked or grouped area chart."""
    fig = px.area(
        df, x=x_col, y=y_col, color=color_col,
        color_discrete_sequence=_PALETTE,
    )
    return _base_layout(fig, title)


def heatmap_chart(df: pd.DataFrame, title: str = "Correlation Heatmap") -> go.Figure:
    """Pearson correlation heatmap for all numeric columns."""
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Not enough numeric columns for a correlation heatmap.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14),
        )
        return _base_layout(fig, title)

    corr = numeric_df.corr()
    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale="RdBu",
            zmid=0,
            text=np.round(corr.values, 2),
            texttemplate="%{text}",
            textfont=dict(size=10),
        )
    )
    return _base_layout(fig, title)


def top_n_bar(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    n: int = 10,
    title: str = "Top Categories",
) -> go.Figure:
    """Horizontal bar showing top-N categories by sum of value_col."""
    grouped = (
        df.groupby(group_col)[value_col]
        .sum()
        .nlargest(n)
        .reset_index()
    )
    fig = px.bar(
        grouped, x=value_col, y=group_col,
        orientation="h", color=value_col,
        color_continuous_scale="Blues",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _base_layout(fig, title)


def funnel_chart(
    df: pd.DataFrame,
    stage_col: str,
    value_col: str,
    title: str = "Funnel",
) -> go.Figure:
    """Funnel chart showing value per stage / category."""
    grouped = df.groupby(stage_col)[value_col].sum().reset_index()
    fig = px.funnel(grouped, x=value_col, y=stage_col,
                    color_discrete_sequence=_PALETTE)
    return _base_layout(fig, title)


# ---------------------------------------------------------------------------
# Chart registry — maps user-facing names to factory functions
# ---------------------------------------------------------------------------

CHART_REGISTRY = {
    "Line Chart": line_chart,
    "Bar Chart": bar_chart,
    "Pie Chart": pie_chart,
    "Scatter Plot": scatter_chart,
    "Histogram": histogram_chart,
    "Box Plot": box_plot,
    "Area Chart": area_chart,
    "Correlation Heatmap": heatmap_chart,
    "Top-N Bar": top_n_bar,
}
