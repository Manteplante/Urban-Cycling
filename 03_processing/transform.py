# Medallion ETL pipeline — Urban Cycling
#
# BRONZE: raw scraped CSVs under 02_data/bronze/{city}/
# SILVER: cleaned and partitioned CSVs under 02_data/silver/{city}/{year}.csv
# GOLD: star-schema dimensions/facts plus notebook exports under 02_data/gold/
#
# Usage:
#     python 03_processing/transform.py              # full pipeline
#     python 03_processing/transform.py --silver     # bronze -> silver only
#     python 03_processing/transform.py --gold       # silver -> gold only

import argparse
import hashlib
import pandas as pd
from pathlib import Path
import re
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    BRONZE_PATH, SILVER_PATH,
    GOLD_PATH, FACTS_PATH, DIMENSIONS_PATH, NOTEBOOK_EXPORTS_PATH,
    CITIES, CITY_ID_MAP, CITY_DISPLAY_MAP, ID_CITY_MAP,
)

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}
DAY_NAMES = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday",
    3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday",
}

# Expected column name variants across city providers
_COLUMN_ALIASES = {
    "started_at":              ["started_at", "start_time", "starttime", "start_datetime"],
    "ended_at":                ["ended_at",   "end_time",   "endtime",   "stopp_datetime", "stop_datetime"],
    "duration_seconds":        ["duration",   "duration_seconds", "seconds"],
    "start_station_id":        ["start_station_id",   "startstation_id"],
    "start_station_name":      ["start_station_name", "startstation_name", "start"],
    "start_station_latitude":  ["start_station_latitude",  "startstation_latitude", "start_ltd"],
    "start_station_longitude": ["start_station_longitude", "startstation_longitude", "start_lon"],
    "end_station_id":          ["end_station_id",   "endstation_id"],
    "end_station_name":        ["end_station_name", "endstation_name", "stopp", "stop"],
    "end_station_latitude":    ["end_station_latitude",  "endstation_latitude", "end_ltd"],
    "end_station_longitude":   ["end_station_longitude", "endstation_longitude", "end_lon"],
}


def _slugify(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return text or "unknown"


def _normalise_station_ref(station_id: object) -> str:
    if pd.isna(station_id):
        return ""
    text = str(station_id).strip()
    if not text or text.lower() == "nan":
        return ""
    return text.lower()


def _normalise_coord(value: object) -> str:
    if pd.isna(value):
        return ""
    try:
        return f"{float(value):.6f}"
    except (TypeError, ValueError):
        return ""


def _city_key(value: object, fallback: str | None = None) -> str:
    if pd.isna(value):
        return fallback or "unknown"

    text = str(value).strip().lower()
    if text in CITY_ID_MAP:
        return text

    try:
        numeric = int(float(text))
    except (TypeError, ValueError):
        numeric = None

    if numeric in ID_CITY_MAP:
        return ID_CITY_MAP[numeric]

    return fallback or text


def _qualify_station_id(
    city_key: str,
    station_name: object,
    station_id: object,
    latitude: object,
    longitude: object,
) -> str:
    station_ref = _normalise_station_ref(station_id)
    station_name_slug = _slugify(station_name)
    lat_key = _normalise_coord(latitude)
    lon_key = _normalise_coord(longitude)

    if station_ref:
        canonical = f"{city_key}|id|{station_ref}"
    else:
        canonical = f"{city_key}|name|{station_name_slug}|lat|{lat_key}|lon|{lon_key}"

    digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:20]
    return f"stn_{digest}"


def _ensure_station_ids(df: pd.DataFrame, fallback_city: str | None = None) -> pd.DataFrame:
    result = df.copy()
    city_keys = [
        _city_key(value, fallback=fallback_city)
        for value in result.get("city_id", pd.Series(index=result.index, dtype=object))
    ]

    start_lat = result.get("start_station_latitude", pd.Series(index=result.index, dtype=object))
    start_lon = result.get("start_station_longitude", pd.Series(index=result.index, dtype=object))
    end_lat = result.get("end_station_latitude", pd.Series(index=result.index, dtype=object))
    end_lon = result.get("end_station_longitude", pd.Series(index=result.index, dtype=object))

    if "start_station_id" not in result.columns:
        result["start_station_id"] = pd.NA
    if "end_station_id" not in result.columns:
        result["end_station_id"] = pd.NA

    if "start_station_name" in result.columns:
        result["start_station_id"] = [
            _qualify_station_id(city_name, station_name, station_id, latitude, longitude)
            for city_name, station_name, station_id, latitude, longitude in zip(
                city_keys,
                result["start_station_name"],
                result["start_station_id"],
                start_lat,
                start_lon,
            )
        ]

    if "end_station_name" in result.columns:
        result["end_station_id"] = [
            _qualify_station_id(city_name, station_name, station_id, latitude, longitude)
            for city_name, station_name, station_id, latitude, longitude in zip(
                city_keys,
                result["end_station_name"],
                result["end_station_id"],
                end_lat,
                end_lon,
            )
        ]

    return result


# Rename columns to canonical names using the alias map.
def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    lower_cols = {c.lower(): c for c in df.columns}
    rename = {}
    for canonical, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_cols and canonical not in df.columns:
                rename[lower_cols[alias]] = canonical
                break
    return df.rename(columns=rename) if rename else df


# ══════════════════════════════════════════════════════════════════════════════
#  STAGE 1 — Bronze  →  Silver
# ══════════════════════════════════════════════════════════════════════════════

def _read_bronze(city: str) -> pd.DataFrame:
    city_path = BRONZE_PATH / city
    if not city_path.exists():
        print(f"  [skip] Bronze folder not found: {city_path}")
        return pd.DataFrame()

    dfs = []
    for csv_file in sorted(city_path.rglob("*.csv")):
        try:
            dfs.append(pd.read_csv(csv_file, low_memory=False))
        except Exception as exc:
            print(f"  [warn] Skipping {csv_file.name}: {exc}")

    dfs = [df for df in dfs if not df.empty]
    if not dfs:
        print(f"  [skip] No CSV files found for {city}")
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)
    print(f"  [bronze] {city}: {len(combined):,} rows from {len(dfs)} file(s)")
    return combined


# Stage 1: Read bronze CSVs, standardise, partition by city + year -> silver.
def run_bronze_to_silver() -> None:
    print("\n[Stage 1]  Bronze → Silver")

    SILVER_PATH.mkdir(parents=True, exist_ok=True)
    total_written = 0

    for city in CITIES:
        raw = _read_bronze(city)
        if raw.empty:
            continue

        df = _normalise_columns(raw)
        df = _ensure_station_ids(df, fallback_city=city)
        df["city_id"] = CITY_ID_MAP[city]

        if "started_at" not in df.columns:
            print(f"  [warn] {city}: no 'started_at' column — skipping")
            continue

        df["started_at"] = pd.to_datetime(df["started_at"], errors="coerce")
        df = df.dropna(subset=["started_at"])
        df["year"] = df["started_at"].dt.year

        city_silver = SILVER_PATH / city
        city_silver.mkdir(parents=True, exist_ok=True)

        for year, grp in df.groupby("year"):
            out = city_silver / f"{int(year)}.csv"
            grp.drop(columns=["year"]).to_csv(out, index=False)
            print(f"  [silver] {city}/{int(year)}.csv → {len(grp):,} rows")
            total_written += len(grp)

    print(f"  Total silver rows: {total_written:,}")


# ══════════════════════════════════════════════════════════════════════════════
#  STAGE 2 — Silver  →  Gold
# ══════════════════════════════════════════════════════════════════════════════

# Combine all silver CSVs into one DataFrame.
def _load_all_silver() -> pd.DataFrame:
    frames = []
    for city in CITIES:
        city_silver = SILVER_PATH / city
        if not city_silver.exists():
            continue
        for csv_file in sorted(city_silver.glob("*.csv")):
            df = pd.read_csv(csv_file, low_memory=False)
            df = _normalise_columns(df)
            df = _ensure_station_ids(df, fallback_city=city)
            df["city_id"] = CITY_ID_MAP[city]
            df["_source_year"] = int(csv_file.stem)
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined["started_at"] = pd.to_datetime(combined["started_at"], errors="coerce")
    return combined


def _build_dim_city() -> pd.DataFrame:
    return pd.DataFrame({
        "city_id":      [1,        2,         3],
        "city_name":    ["oslo",   "bergen",  "trondheim"],
        "display_name": ["Oslo",   "Bergen",  "Trondheim"],
        "country":      ["Norway", "Norway",  "Norway"],
    })


def _build_dim_stations(df: pd.DataFrame) -> pd.DataFrame:
    df = _ensure_station_ids(df)
    start = df[["start_station_id","start_station_name",
                "start_station_latitude","start_station_longitude","city_id"]].copy()
    start.columns = ["station_id","station_name","latitude","longitude","city_id"]

    end = df[["end_station_id","end_station_name",
              "end_station_latitude","end_station_longitude","city_id"]].copy()
    end.columns = ["station_id","station_name","latitude","longitude","city_id"]

    stations = (
        pd.concat([start, end], ignore_index=True)
        .dropna(subset=["station_id","station_name","latitude","longitude"])
    )
    stations["station_id"] = stations["station_id"].astype(str)
    return (
        stations
        .drop_duplicates(subset=["station_id", "city_id"], keep="last")
        .sort_values(["city_id", "station_id"])
        .reset_index(drop=True)
    )


def _build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    dates = pd.DatetimeIndex(
        sorted(df["started_at"].dt.normalize().dropna().unique())
    )
    return pd.DataFrame({
        "date_id":     dates.strftime("%Y%m%d").astype(int),
        "date":        dates.date,
        "year":        dates.year,
        "month":       dates.month,
        "month_name":  dates.month.map(MONTH_NAMES),
        "day":         dates.day,
        "day_of_week": dates.dayofweek,
        "day_name":    dates.dayofweek.map(DAY_NAMES),
        "is_weekend":  (dates.dayofweek >= 5).astype(int),
        "quarter":     dates.quarter,
    })


# Return {year: DataFrame} for the fact_trips tables.
def _build_fact_trips(df: pd.DataFrame) -> dict:
    out = _ensure_station_ids(df)
    out["date_id"]           = out["started_at"].dt.strftime("%Y%m%d").astype(int)
    out["start_hour"]        = out["started_at"].dt.hour
    out["year"]              = out["started_at"].dt.year
    out["start_station_id"]  = out["start_station_id"].astype(str)
    out["end_station_id"]    = out["end_station_id"].astype(str)

    if "duration_seconds" not in out.columns and "ended_at" in out.columns:
        out["ended_at"] = pd.to_datetime(out["ended_at"], errors="coerce")
        out["duration_seconds"] = (out["ended_at"] - out["started_at"]).dt.total_seconds()

    if "trip_id" not in out.columns:
        out["trip_id"] = [f"trip_{i}" for i in range(len(out))]

    keep = ["trip_id", "city_id", "start_station_id", "end_station_id",
            "date_id","start_hour","duration_seconds","year"]
    out = out[[c for c in keep if c in out.columns]].reset_index(drop=True)

    return {
        int(year): grp.drop(columns=["year"]).reset_index(drop=True)
        for year, grp in out.groupby("year")
    }


# Build top N intra-city station-to-station route patterns per city/year.
def _build_fact_top_trip_patterns(df: pd.DataFrame, n: int = 10, years: list[int] | None = None) -> pd.DataFrame:
    out = _ensure_station_ids(df)

    required = [
        "city_id",
        "start_station_id",
        "start_station_name",
        "start_station_latitude",
        "start_station_longitude",
        "end_station_id",
        "end_station_name",
        "end_station_latitude",
        "end_station_longitude",
        "started_at",
    ]
    if any(col not in out.columns for col in required):
        return pd.DataFrame()

    out = out.dropna(
        subset=[
            "city_id",
            "start_station_id",
            "end_station_id",
            "start_station_latitude",
            "start_station_longitude",
            "end_station_latitude",
            "end_station_longitude",
            "started_at",
        ]
    ).copy()
    if out.empty:
        return pd.DataFrame()

    out["city_id"] = pd.to_numeric(out["city_id"], errors="coerce")
    out["year"] = pd.to_datetime(out["started_at"], errors="coerce").dt.year
    out = out.dropna(subset=["city_id", "year"])
    if out.empty:
        return pd.DataFrame()

    out["city_id"] = out["city_id"].astype(int)
    out["year"] = out["year"].astype(int)

    if years:
        year_filter = set(int(y) for y in years)
        out = out[out["year"].isin(year_filter)].copy()
        if out.empty:
            return pd.DataFrame()

    if "duration_seconds" not in out.columns and "ended_at" in out.columns:
        out["ended_at"] = pd.to_datetime(out["ended_at"], errors="coerce")
        out["duration_seconds"] = (out["ended_at"] - out["started_at"]).dt.total_seconds()

    group_cols = [
        "city_id",
        "year",
        "start_station_id",
        "start_station_name",
        "start_station_latitude",
        "start_station_longitude",
        "end_station_id",
        "end_station_name",
        "end_station_latitude",
        "end_station_longitude",
    ]

    patterns = (
        out.groupby(group_cols, dropna=False)
        .agg(
            trip_count=("start_station_id", "size"),
            avg_duration_seconds=("duration_seconds", "mean"),
            median_duration_seconds=("duration_seconds", "median"),
        )
        .reset_index()
    )
    if patterns.empty:
        return patterns

    patterns["rank"] = (
        patterns.groupby(["city_id", "year"])["trip_count"]
        .rank(method="dense", ascending=False)
        .astype(int)
    )
    patterns = patterns[patterns["rank"] <= int(n)].copy()

    totals = (
        out.groupby(["city_id", "year"], as_index=False)
        .size()
        .rename(columns={"size": "city_year_trips"})
    )
    patterns = patterns.merge(totals, on=["city_id", "year"], how="left")
    patterns["percent_of_city_trips"] = (
        (patterns["trip_count"] / patterns["city_year_trips"]) * 100
    ).round(2)

    city_name_map = {v: CITY_DISPLAY_MAP[k] for k, v in CITY_ID_MAP.items()}
    patterns["city_name"] = patterns["city_id"].map(city_name_map)

    patterns = patterns.rename(
        columns={
            "start_station_latitude": "start_lat",
            "start_station_longitude": "start_lon",
            "end_station_latitude": "end_lat",
            "end_station_longitude": "end_lon",
        }
    )

    keep_cols = [
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
    ]

    return (
        patterns[keep_cols]
        .sort_values(["city_id", "year", "rank", "trip_count"], ascending=[True, True, True, False])
        .reset_index(drop=True)
    )


# Stage 2: Read all silver CSVs -> build star schema -> write gold.
def run_silver_to_gold() -> None:
    print("\n[Stage 2]  Silver → Gold")

    for path in [FACTS_PATH, DIMENSIONS_PATH, NOTEBOOK_EXPORTS_PATH]:
        path.mkdir(parents=True, exist_ok=True)

    all_data = _load_all_silver()
    if all_data.empty:
        print("  [!] No silver data found. Run Stage 1 first.")
        return

    print(f"  Combined silver rows: {len(all_data):,}")

    # Dimensions
    dim_city     = _build_dim_city()
    dim_stations = _build_dim_stations(all_data)
    dim_date     = _build_dim_date(all_data)

    dim_city.to_csv(DIMENSIONS_PATH / "dim_city.csv", index=False)
    dim_stations.to_csv(DIMENSIONS_PATH / "dim_stations.csv", index=False)
    dim_date.to_csv(DIMENSIONS_PATH / "dim_date.csv", index=False)

    print(f"  [gold/dim] dim_city:     {len(dim_city):>6,} rows")
    print(f"  [gold/dim] dim_stations: {len(dim_stations):>6,} rows")
    print(f"  [gold/dim] dim_date:     {len(dim_date):>6,} rows")

    # Facts — one file per year
    facts_by_year = _build_fact_trips(all_data)
    total_trips   = 0
    for year, fact_df in sorted(facts_by_year.items()):
        fact_df.to_csv(FACTS_PATH / f"fact_trips_{year}.csv", index=False)
        print(f"  [gold/fact] fact_trips_{year}: {len(fact_df):>8,} trips")
        total_trips += len(fact_df)

    top_patterns = _build_fact_top_trip_patterns(all_data, n=10)
    top_patterns_path = FACTS_PATH / "fact_top_trip_patterns.csv"
    top_patterns.to_csv(top_patterns_path, index=False)
    print(f"  [gold/fact] fact_top_trip_patterns: {len(top_patterns):>8,} rows")

    print(f"  Total gold trips: {total_trips:,}")


# ══════════════════════════════════════════════════════════════════════════════
#  Full pipeline
# ══════════════════════════════════════════════════════════════════════════════

def run_etl(silver: bool = True, gold: bool = True) -> None:
    print("=" * 66)
    print("  Urban Cycling — Medallion ETL")
    print("  Bronze path : " + str(BRONZE_PATH))
    print("  Silver path : " + str(SILVER_PATH))
    print("  Gold path   : " + str(GOLD_PATH))
    print("=" * 66)
    if silver:
        run_bronze_to_silver()
    if gold:
        run_silver_to_gold()
    print("\n  Done.\n")


# Incremental mode: rebuild only fact_top_trip_patterns.csv from silver.
def run_gold_top_patterns_only(years: list[int] | None = None) -> None:
    print("\n[Stage 2b]  Silver → Gold (top patterns only)")
    FACTS_PATH.mkdir(parents=True, exist_ok=True)

    all_data = _load_all_silver()
    if all_data.empty:
        print("  [!] No silver data found. Run Stage 1 first.")
        return

    top_patterns = _build_fact_top_trip_patterns(all_data, n=10, years=years)
    top_patterns_path = FACTS_PATH / "fact_top_trip_patterns.csv"
    top_patterns.to_csv(top_patterns_path, index=False)

    years_txt = f" for years {sorted(set(years))}" if years else ""
    print(f"  [gold/fact] fact_top_trip_patterns{years_txt}: {len(top_patterns):>8,} rows")
    print("\n  Done.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Urban Cycling Medallion ETL")
    parser.add_argument("--silver", action="store_true", help="Bronze → Silver only")
    parser.add_argument("--gold",   action="store_true", help="Silver → Gold only")
    parser.add_argument("--top-patterns", action="store_true", help="Rebuild only fact_top_trip_patterns.csv")
    parser.add_argument("--years", nargs="+", type=int, help="Optional year filter for --top-patterns")
    args = parser.parse_args()

    if args.top_patterns:
        run_gold_top_patterns_only(years=args.years)
    elif args.silver and not args.gold:
        run_etl(silver=True, gold=False)
    elif args.gold and not args.silver:
        run_etl(silver=False, gold=True)
    else:
        run_etl()


