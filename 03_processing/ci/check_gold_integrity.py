from __future__ import annotations

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FACTS_ROOT = PROJECT_ROOT / "02_data" / "gold" / "facts"

REQUIRED_COLS = {
    "rank",
    "city_id",
    "city_name",
    "year",
    "start_station_id",
    "start_station_name",
    "start_lat",
    "start_lon",
    "end_station_id",
    "end_station_name",
    "end_lat",
    "end_lon",
    "trip_count",
    "percent_of_city_trips",
    "avg_duration_seconds",
    "median_duration_seconds",
}


def check_top_trip_patterns() -> int:
    path = FACTS_ROOT / "fact_top_trip_patterns.csv"
    if not path.exists():
        print("ERROR: Missing 02_data/gold/facts/fact_top_trip_patterns.csv")
        return 1

    df = pd.read_csv(path)
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        print(f"ERROR: Missing required columns: {sorted(missing)}")
        return 1

    if df.empty:
        print("ERROR: fact_top_trip_patterns.csv is empty")
        return 1

    null_coord_rows = df[df[["start_lat", "start_lon", "end_lat", "end_lon"]].isna().any(axis=1)]
    if not null_coord_rows.empty:
        print(f"ERROR: Found {len(null_coord_rows)} rows with null route coordinates")
        return 1

    bad_ranks = df[(df["rank"] < 1) | (df["rank"] > 10)]
    if not bad_ranks.empty:
        print(f"ERROR: Found {len(bad_ranks)} rows with rank outside 1..10")
        return 1

    for (city_id, year), grp in df.groupby(["city_id", "year"]):
        if int(grp["rank"].max()) > 10:
            print(f"ERROR: City {city_id} year {year} has rank above 10")
            return 1

    print(f"OK: fact_top_trip_patterns.csv passed integrity checks ({len(df):,} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(check_top_trip_patterns())
