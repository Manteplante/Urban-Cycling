"""Reusable Plotly chart components for the Urban Cycling dashboard."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

COLORS = {
    "primary":   "#FF6B6B",
    "secondary": "#4ECDC4",
    "accent":    "#45B7D1",
    "dark":      "#2C3E50",
}


def bar_hourly(df: pd.DataFrame) -> go.Figure:
    """Bar chart of trips by hour of day."""
    fig = px.bar(
        df, x="start_hour", y="trips",
        title="Trips by Hour of Day",
        labels={"start_hour": "Hour", "trips": "Number of Trips"},
        color="trips",
        color_continuous_scale="Reds",
    )
    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        xaxis=dict(tickmode="linear", dtick=1),
        plot_bgcolor="white",
        margin=dict(t=40),
    )
    return fig


def bar_daily(df: pd.DataFrame) -> go.Figure:
    """Bar chart of trips by day of week."""
    fig = px.bar(
        df, x="day_name", y="trips",
        title="Trips by Day of Week",
        labels={"day_name": "Day", "trips": "Number of Trips"},
        color="trips",
        color_continuous_scale="Blues",
    )
    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        plot_bgcolor="white",
        margin=dict(t=40),
    )
    return fig


def line_monthly(df: pd.DataFrame) -> go.Figure:
    """Line chart of monthly trip volume."""
    df = df.copy()
    df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
    fig = px.line(
        df, x="period", y="trips",
        title="Monthly Trip Volume",
        labels={"period": "Month", "trips": "Number of Trips"},
        markers=True,
        color_discrete_sequence=[COLORS["primary"]],
    )
    fig.update_layout(
        plot_bgcolor="white",
        xaxis_tickangle=-45,
        margin=dict(t=40),
    )
    return fig


def bar_top_routes(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of top station-to-station routes."""
    df = df.copy()
    df["route"] = df["start_station_name"] + " → " + df["end_station_name"]
    fig = px.bar(
        df, x="trips", y="route",
        orientation="h",
        title="Top Routes by Trip Count",
        labels={"trips": "Trips", "route": "Route"},
        color="trips",
        color_continuous_scale="Oranges",
    )
    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white",
        height=max(300, len(df) * 36),
        margin=dict(t=40),
    )
    return fig


def histogram_duration(df: pd.DataFrame, max_minutes: float = 60.0) -> go.Figure:
    """Histogram of trip durations capped at max_minutes."""
    minutes = df["duration_seconds"].dropna() / 60
    minutes = minutes[minutes <= max_minutes]
    fig = px.histogram(
        minutes, nbins=60,
        title=f"Trip Duration Distribution (≤ {int(max_minutes)} min)",
        labels={"value": "Duration (minutes)", "count": "Count"},
        color_discrete_sequence=[COLORS["secondary"]],
    )
    fig.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        margin=dict(t=40),
    )
    return fig


def scatter_regression(
    x_vals: list,
    y_vals: list,
    slope: float,
    intercept: float,
    r2: float,
    x_labels: list = None,
    title: str = "",
) -> go.Figure:
    """Scatter plot with a linear trend line."""
    if not x_vals:
        return go.Figure()

    x_range = [x_vals[0], x_vals[-1]]
    y_range = [intercept + slope * x_range[0], intercept + slope * x_range[1]]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals,
        mode="markers",
        marker=dict(size=10, color=COLORS["primary"]),
        name="Trips",
    ))
    fig.add_trace(go.Scatter(
        x=x_range, y=y_range,
        mode="lines",
        line=dict(color=COLORS["dark"], dash="dash"),
        name=f"Trend (R²={r2:.3f})",
    ))
    if x_labels:
        fig.update_xaxes(tickvals=x_vals, ticktext=x_labels, tickangle=-45)
    fig.update_layout(
        title=title or "Trip Trend",
        xaxis_title="Month",
        yaxis_title="Trips",
        plot_bgcolor="white",
        margin=dict(t=50),
    )
    return fig
