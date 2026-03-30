# 03_processing/workspace/utils.py
# Workspace analysis toolkit for notebooks in 03_processing/workspace.
#
# Supports layer loaders (bronze/silver/gold), export helpers, and common
# analysis/plot utilities aligned with the app data model.

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ── Path resolution ────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent   # 03_processing/workspace/
_PROC = _HERE.parent            # 03_processing/
sys.path.insert(0, str(_PROC))
sys.path.insert(0, str(_PROC.parent / "04_app"))

from config import CITIES, CITY_DISPLAY_MAP, FACTS_PATH, SILVER_PATH
from notebook_bridge import (
    export_df,
    export_figure,
    list_exports,
    load_bronze as _load_bronze,
    load_gold as _load_gold,
    load_silver as _load_silver,
)

try:
    from services.gold import gold as _app_gold
except Exception:
    _app_gold = None

__all__ = [
    # loaders
    "load", "load_bronze", "load_silver", "load_gold", "load_app_ready",
    # exports
    "export_df", "export_figure", "list_exports",
    # analysis helpers
    "describe", "feature_matrix",
    # plots
    "plot_hourly", "plot_monthly", "plot_top_stations",
    "plot_duration_dist", "plot_city_comparison",
    # constants
    "CITIES", "CITY_DISPLAY_MAP",
]


# ══════════════════════════════════════════════════════════════════════════════
#  Loaders
# ══════════════════════════════════════════════════════════════════════════════

# All raw bronze CSVs for a city, concatenated.
def load_bronze(city: str) -> pd.DataFrame:
    return _load_bronze(city)


# Cleaned silver data for a city (optionally filtered by year).
def load_silver(city: str, year: int = None) -> pd.DataFrame:
    return _load_silver(city, year)


# Load a gold table by name, e.g. dim_city or fact_trips_2024.
def load_gold(table: str) -> pd.DataFrame:
    return _load_gold(table)


# Load the same denormalised dataset shape used by the Streamlit app.
def load_app_ready(
    city: str | None = None,
    years: list[int] | None = None,
    months: list[int] | None = None,
) -> pd.DataFrame:
    if _app_gold is None:
        raise ImportError(
            "Could not import Streamlit gold catalog. "
            "Ensure 04_app/services/gold.py exists and dependencies are installed."
        )

    query = _app_gold.query()
    if city:
        query = query.city(city)
    if years:
        query = query.years(years)
    if months:
        query = query.months(months)
    return query.load()


# Primary data loader for workspace analysis.
# city: oslo|bergen|trondheim|None, year: int|None, layer: silver|gold.
def load(city: str = None, year: int = None, layer: str = "silver") -> pd.DataFrame:
    if layer == "gold":
        if year is not None:
            return _load_gold(f"fact_trips_{year}")
        frames = [
            pd.read_csv(f, low_memory=False)
            for f in sorted(FACTS_PATH.glob("fact_trips_*.csv"))
        ]
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    # Silver layer
    if city:
        return _load_silver(city, year)

    frames = []
    for c in CITIES:
        try:
            df = _load_silver(c, year)
            df["city"] = c
            frames.append(df)
        except (FileNotFoundError, ValueError):
            pass
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
#  Analysis helpers
# ══════════════════════════════════════════════════════════════════════════════

# Extended describe: adds null counts, null %, and dtype columns.
def describe(df: pd.DataFrame) -> pd.DataFrame:
    stats = df.describe(include="all").T
    stats["nulls"]  = df.isnull().sum()
    stats["null_%"] = (df.isnull().mean() * 100).round(2)
    stats["dtype"]  = df.dtypes
    return stats


# Build an ML-ready (X, y) tuple from a silver or gold DataFrame.
# Adds derived time features from started_at when available.
def feature_matrix(
    df: pd.DataFrame,
    target: str = "duration_seconds",
) -> tuple:
    df = df.copy()

    if "started_at" in df.columns:
        df["started_at"]  = pd.to_datetime(df["started_at"], errors="coerce")
        df["hour"]        = df["started_at"].dt.hour
        df["day_of_week"] = df["started_at"].dt.dayofweek
        df["month"]       = df["started_at"].dt.month
        df["is_weekend"]  = (df["day_of_week"] >= 5).astype(int)

    feature_cols = [
        c for c in ["hour", "day_of_week", "month", "is_weekend", "city_id"]
        if c in df.columns
    ]
    drop_na_cols = feature_cols + ([target] if target in df.columns else [])
    df = df.dropna(subset=drop_na_cols)

    X = df[feature_cols]
    y = df[target] if target in df.columns else pd.Series(dtype=float)
    return X, y


# ══════════════════════════════════════════════════════════════════════════════
#  Plots  (return plt.Figure — call fig.savefig() or export_figure() to save)
# ══════════════════════════════════════════════════════════════════════════════

def _ensure_datetime(df: pd.DataFrame, col: str = "started_at") -> pd.DataFrame:
    df = df.copy()
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


# Bar chart of trip counts by hour (0-23).
def plot_hourly(df: pd.DataFrame, title: str = "Trips by Hour of Day") -> plt.Figure:
    df = _ensure_datetime(df)
    hourly = (
        df["started_at"].dt.hour
        .value_counts()
        .sort_index()
        .reindex(range(24), fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.bar(hourly.index, hourly.values, color="#1f77b4", alpha=0.85)
    ax.set(xlabel="Hour of Day", ylabel="Trips", title=title, xticks=range(24))
    fig.tight_layout()
    return fig


# Line chart of trip volume per calendar month.
def plot_monthly(df: pd.DataFrame, title: str = "Monthly Trip Volume") -> plt.Figure:
    df = _ensure_datetime(df)
    monthly = df["started_at"].dt.to_period("M").value_counts().sort_index()
    labels  = monthly.index.astype(str)

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(labels, monthly.values, marker="o", linewidth=2, color="#1f77b4")
    ax.fill_between(range(len(monthly)), monthly.values, alpha=0.15, color="#1f77b4")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set(ylabel="Trips", title=title)
    fig.tight_layout()
    return fig


# Horizontal bar chart of the top N stations by trip count.
def plot_top_stations(
    df: pd.DataFrame,
    n: int = 10,
    col: str = "start_station_name",
    title: str = None,
) -> plt.Figure:
    top   = df[col].value_counts().head(n)
    title = title or f"Top {n} Departure Stations"

    fig, ax = plt.subplots(figsize=(10, max(3, n * 0.45)))
    ax.barh(top.index[::-1], top.values[::-1], color="#2ca02c", alpha=0.85)
    ax.set(xlabel="Trips", title=title)
    fig.tight_layout()
    return fig


# Histogram of trip durations in minutes, capped at max_minutes.
def plot_duration_dist(
    df: pd.DataFrame,
    max_minutes: int = 60,
    title: str = "Trip Duration Distribution",
) -> plt.Figure:
    if "duration_seconds" not in df.columns:
        raise ValueError("DataFrame must contain a 'duration_seconds' column")

    mins = df["duration_seconds"].div(60)
    mins = mins[(mins > 0) & (mins <= max_minutes)]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(mins, bins=60, color="#ff7f0e", alpha=0.85, edgecolor="white")
    median = mins.median()
    ax.axvline(median, color="red", linestyle="--", label=f"Median: {median:.1f} min")
    ax.set(xlabel="Duration (minutes)", ylabel="Count", title=title)
    ax.legend()
    fig.tight_layout()
    return fig


# Bar chart comparing total trip volumes per city.
def plot_city_comparison(
    df: pd.DataFrame,
    title: str = "Trip Volume by City",
) -> plt.Figure:
    col = "city" if "city" in df.columns else "city_id"
    city_counts = df[col].value_counts().sort_values(ascending=False)

    colours = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(
        city_counts.index.astype(str),
        city_counts.values,
        color=colours[: len(city_counts)],
    )
    ax.set(xlabel="City", ylabel="Trips", title=title)
    fig.tight_layout()
    return fig
