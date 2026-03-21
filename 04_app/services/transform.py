"""
App-level aggregation helpers.
These functions take a denormalised trips DataFrame (from services/gold)
and return smaller DataFrames ready for specific visualisations.
"""

import pandas as pd


def station_trip_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Departures + arrivals per station, with lat/lon for mapping."""
    if df.empty:
        return pd.DataFrame()

    dep_cols = ["start_station_id", "start_station_name", "start_lat", "start_lon"]
    arr_cols = ["end_station_id",   "end_station_name",   "end_lat",   "end_lon"]

    if not all(c in df.columns for c in dep_cols + arr_cols):
        return pd.DataFrame()

    departures = (
        df.groupby(dep_cols)
        .size()
        .reset_index(name="departures")
        .rename(columns={
            "start_station_id": "station_id",
            "start_station_name": "station_name",
            "start_lat": "latitude",
            "start_lon": "longitude",
        })
    )
    arrivals = (
        df.groupby(arr_cols)
        .size()
        .reset_index(name="arrivals")
        .rename(columns={
            "end_station_id": "station_id",
            "end_station_name": "station_name",
            "end_lat": "latitude",
            "end_lon": "longitude",
        })
    )

    merged = departures.merge(
        arrivals, on=["station_id", "station_name", "latitude", "longitude"], how="outer"
    )
    merged["departures"]  = merged["departures"].fillna(0).astype(int)
    merged["arrivals"]    = merged["arrivals"].fillna(0).astype(int)
    merged["total_trips"] = merged["departures"] + merged["arrivals"]

    return (
        merged
        .dropna(subset=["latitude", "longitude"])
        .sort_values("total_trips", ascending=False)
        .reset_index(drop=True)
    )


def hourly_trips(df: pd.DataFrame) -> pd.DataFrame:
    """Trip counts grouped by hour of day (0-23)."""
    if df.empty or "start_hour" not in df.columns:
        return pd.DataFrame({"start_hour": range(24), "trips": [0] * 24})
    return df.groupby("start_hour").size().reset_index(name="trips")


def daily_trips(df: pd.DataFrame) -> pd.DataFrame:
    """Trip counts grouped by day of week, ordered Mon-Sun."""
    if df.empty or "day_name" not in df.columns:
        return pd.DataFrame()
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    result = df.groupby(["day_of_week", "day_name"]).size().reset_index(name="trips")
    result["day_name"] = pd.Categorical(result["day_name"], categories=day_order, ordered=True)
    return result.sort_values("day_name")


def monthly_trips(df: pd.DataFrame) -> pd.DataFrame:
    """Trip counts grouped by year + month, sorted chronologically."""
    if df.empty or "month" not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby(["year", "month", "month_name"])
        .size()
        .reset_index(name="trips")
        .sort_values(["year", "month"])
        .reset_index(drop=True)
    )


def top_routes(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N start→end station pairs by trip count."""
    if df.empty or "start_station_name" not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby(["start_station_name", "end_station_name"])
        .size()
        .reset_index(name="trips")
        .sort_values("trips", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )


def duration_stats(df: pd.DataFrame) -> dict:
    """Summary statistics for trip duration (in minutes)."""
    if df.empty or "duration_seconds" not in df.columns:
        return {}
    minutes = df["duration_seconds"].dropna() / 60
    return {
        "mean_minutes":   round(float(minutes.mean()), 1),
        "median_minutes": round(float(minutes.median()), 1),
        "p90_minutes":    round(float(minutes.quantile(0.9)), 1),
        "max_minutes":    round(float(minutes.max()), 1),
    }
