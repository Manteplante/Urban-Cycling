# App-level aggregation helpers.
# These functions take a denormalised trips DataFrame (from services/gold)
# and return smaller DataFrames ready for specific visualisations.

import pandas as pd


# Departures + arrivals per station, with lat/lon for mapping.
def station_trip_counts(df: pd.DataFrame) -> pd.DataFrame:
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


# Trip counts grouped by hour of day (0-23).
def hourly_trips(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "start_hour" not in df.columns:
        return pd.DataFrame({"start_hour": range(24), "trips": [0] * 24})
    return df.groupby("start_hour").size().reset_index(name="trips")


# Trip counts grouped by day of week, ordered Mon-Sun.
def daily_trips(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "day_name" not in df.columns:
        return pd.DataFrame()
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    result = df.groupby(["day_of_week", "day_name"]).size().reset_index(name="trips")
    result["day_name"] = pd.Categorical(result["day_name"], categories=day_order, ordered=True)
    return result.sort_values("day_name")


# Trip counts grouped by year + month, sorted chronologically.
def monthly_trips(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "month" not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby(["year", "month", "month_name"])
        .size()
        .reset_index(name="trips")
        .sort_values(["year", "month"])
        .reset_index(drop=True)
    )


# Top N start→end station pairs by trip count.
def top_routes(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
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


# Build stable route keys and user-facing labels for map slicers.
def route_slicer_options(patterns_df: pd.DataFrame) -> pd.DataFrame:
    if patterns_df.empty:
        return pd.DataFrame()

    required = [
        "rank",
        "city_name",
        "year",
        "start_station_name",
        "end_station_name",
        "trip_count",
    ]
    if any(col not in patterns_df.columns for col in required):
        return pd.DataFrame()

    out = patterns_df.copy()
    out["route_key"] = (
        out["city_name"].astype(str)
        + "|"
        + out["year"].astype(str)
        + "|"
        + out["start_station_name"].astype(str)
        + "|"
        + out["end_station_name"].astype(str)
    )
    out["route_label"] = out.apply(
        lambda r: (
            f"#{int(r['rank'])} {r['start_station_name']} -> {r['end_station_name']} "
            f"({int(r['trip_count']):,} trips, {int(r['year'])})"
        ),
        axis=1,
    )
    return out


# Return only selected route lines, preserving map payload columns.
def selected_route_lines(patterns_df: pd.DataFrame, selected_route_keys: list[str]) -> pd.DataFrame:
    if patterns_df.empty or not selected_route_keys:
        return pd.DataFrame()

    if "route_key" not in patterns_df.columns:
        return pd.DataFrame()

    keep_cols = [
        "route_key",
        "route_label",
        "rank",
        "city_name",
        "year",
        "start_station_name",
        "end_station_name",
        "start_lat",
        "start_lon",
        "end_lat",
        "end_lon",
        "trip_count",
        "avg_duration_seconds",
        "median_duration_seconds",
    ]
    keep_cols = [c for c in keep_cols if c in patterns_df.columns]
    return (
        patterns_df[patterns_df["route_key"].isin(selected_route_keys)][keep_cols]
        .dropna(subset=[c for c in ["start_lat", "start_lon", "end_lat", "end_lon"] if c in keep_cols])
        .reset_index(drop=True)
    )


# Summary statistics for trip duration (in minutes).
def duration_stats(df: pd.DataFrame) -> dict:
    if df.empty or "duration_seconds" not in df.columns:
        return {}
    minutes = df["duration_seconds"].dropna() / 60
    return {
        "mean_minutes":   round(float(minutes.mean()), 1),
        "median_minutes": round(float(minutes.median()), 1),
        "p90_minutes":    round(float(minutes.quantile(0.9)), 1),
        "max_minutes":    round(float(minutes.max()), 1),
    }
