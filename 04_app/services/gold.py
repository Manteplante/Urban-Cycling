# services/gold.py — Urban Cycling Gold Layer Catalog
# Single import point for gold-layer access in the Streamlit app.
# Use gold.query() for joined data, or gold.{trips,stations,dates,cities}()
# for direct table access.

from __future__ import annotations

import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

from services.gcs_storage import gcs_enabled, gcs_exists, gcs_list, gcs_read_csv

try:
    import streamlit as st
    import streamlit.runtime as st_runtime
except Exception:
    st = None
    st_runtime = None

# ── Paths ──────────────────────────────────────────────────────────────────────
_PROJECT_ROOT    = Path(__file__).parents[2]
load_dotenv(_PROJECT_ROOT / ".env")

_AVAILABLE_YEARS = (os.getenv("AVAILABLE_YEARS") or "").strip()


def _read_csv_remote(relative_path: str, **kwargs) -> pd.DataFrame:
    if not gcs_enabled() or not gcs_exists(relative_path):
        return pd.DataFrame()
    return gcs_read_csv(relative_path, **kwargs)


def cache_data(ttl: int = 3600, max_entries: int | None = None):
    # Notebook and script contexts should not depend on Streamlit runtime state.
    if st is None:
        def decorator(func):
            return func
        return decorator

    try:
        if st_runtime is None or not st_runtime.exists():
            def decorator(func):
                return func
            return decorator
    except Exception:
        pass

    return st.cache_data(ttl=ttl, max_entries=max_entries)


def _optimize_fact_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    optimized = df.copy()

    int_columns = optimized.select_dtypes(include=["int", "int64", "Int64"]).columns
    for column in int_columns:
        optimized[column] = pd.to_numeric(optimized[column], downcast="integer")

    float_columns = optimized.select_dtypes(include=["float", "float64", "Float64"]).columns
    for column in float_columns:
        optimized[column] = pd.to_numeric(optimized[column], downcast="float")

    return optimized


def _requested_columns(required_columns: tuple[str, ...] | None) -> set[str]:
    return set(required_columns or ())


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _debug_memory_enabled() -> bool:
    env_raw = (os.getenv("APP_DEBUG_MEMORY") or "").strip()
    return bool(env_raw) and _is_truthy(env_raw)


def _dataframe_memory_mb(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    return float(df.memory_usage(deep=True).sum()) / (1024 * 1024)


def _emit_memory_debug(message: str) -> None:
    if not message or not _debug_memory_enabled():
        return
    print(f"[app-memory] {message}")

_SCHEMA_REFERENCE_LINES = [
    "trip_id",
    "city_name",
    "start_station_id",
    "start_station_name",
    "start_lat",
    "start_lon",
    "end_station_id",
    "end_station_name",
    "end_lat",
    "end_lon",
    "date_id",
    "date",
    "year",
    "month",
    "month_name",
    "day_of_week",
    "day_name",
    "is_weekend",
    "quarter",
    "start_hour",
    "duration_seconds",
]


# ══════════════════════════════════════════════════════════════════════════════
#  Low-level cached loaders  (internal — use the catalog instead)
# ══════════════════════════════════════════════════════════════════════════════

@cache_data(ttl=3600, max_entries=1)
def cities() -> pd.DataFrame:
    remote_df = _read_csv_remote("dimensions/dim_city.csv")
    if not remote_df.empty:
        return remote_df

    return pd.DataFrame({
        "city_id":      [1,       2,         3],
        "city_name":    ["oslo",  "bergen",  "trondheim"],
        "display_name": ["Oslo",  "Bergen",  "Trondheim"],
        "country":      ["Norway","Norway",  "Norway"],
    })


@cache_data(ttl=3600, max_entries=1)
def stations() -> pd.DataFrame:
    df = _read_csv_remote("dimensions/dim_stations.csv")
    if df.empty:
        return pd.DataFrame(columns=["station_id","station_name","latitude","longitude","city_id"])
    return df


@cache_data(ttl=3600, max_entries=1)
def dates() -> pd.DataFrame:
    return _read_csv_remote("dimensions/dim_date.csv", parse_dates=["date"])


@cache_data(ttl=900, max_entries=1)
def available_years() -> list[int]:
    if gcs_enabled():
        entries = gcs_list("facts")
        years: list[int] = []
        for entry in entries:
            name = Path(str(entry.get("name") or "")).name
            if not name.startswith("fact_trips_"):
                continue
            stem = Path(name).stem
            token = stem.split("_")[-1]
            try:
                years.append(int(token))
            except ValueError:
                continue

        if years:
            return sorted(set(years))

    if not _AVAILABLE_YEARS:
        return []

    parsed: list[int] = []
    for token in _AVAILABLE_YEARS.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            parsed.append(int(token))
        except ValueError:
            continue

    return sorted(set(parsed))


@cache_data(ttl=900, max_entries=3)
def facts(years: tuple[int, ...]) -> pd.DataFrame:
    frames = []
    for yr in years:
        remote_relative_path = f"facts/fact_trips_{yr}.csv"

        if not gcs_enabled() or not gcs_exists(remote_relative_path):
            continue

        df = gcs_read_csv(remote_relative_path)
        if not df.empty:
            df["year"] = yr
            frames.append(_optimize_fact_frame(df))

    result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    _emit_memory_debug(
        f"facts cache-miss years={list(years)} rows={len(result):,} cols={len(result.columns)} mem_mb={_dataframe_memory_mb(result):.2f}"
    )
    return result


@cache_data(ttl=900, max_entries=2)
def top_trip_patterns() -> pd.DataFrame:
    result = _read_csv_remote("facts/fact_top_trip_patterns.csv")
    _emit_memory_debug(
        f"top_trip_patterns cache-miss rows={len(result):,} cols={len(result.columns)} mem_mb={_dataframe_memory_mb(result):.2f}"
    )
    return result


def joined(
    city_ids: tuple[int, ...],
    years: tuple[int, ...],
    required_columns: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    # Avoid caching the fully denormalised table: it is the largest object in the app.
    requested = _requested_columns(required_columns)
    facts_df = facts(years)
    if facts_df.empty:
        return pd.DataFrame()

    if city_ids:
        facts_df = facts_df[facts_df["city_id"].isin(city_ids)]
    if facts_df.empty:
        return pd.DataFrame()

    if requested:
        fact_columns = set(requested)
        if "city_name" in requested:
            fact_columns.add("city_id")
        if requested.intersection({"start_station_name", "start_lat", "start_lon"}):
            fact_columns.update({"city_id", "start_station_id"})
        if requested.intersection({"end_station_name", "end_lat", "end_lon"}):
            fact_columns.update({"city_id", "end_station_id"})
        if requested.intersection({"date", "month", "month_name", "day_of_week", "day_name", "is_weekend", "quarter"}):
            fact_columns.add("date_id")

        present_fact_columns = [column for column in facts_df.columns if column in fact_columns]
        facts_df = facts_df[present_fact_columns]

    df = facts_df.copy()

    # city name
    if not requested or "city_name" in requested:
        dim_city = cities()
        df = df.merge(
            dim_city[["city_id", "display_name"]].rename(columns={"display_name": "city_name"}),
            on="city_id", how="left",
        )

    # start station
    if not requested or requested.intersection({"start_station_name", "start_lat", "start_lon"}):
        dim_stations = stations()
        df["start_station_id"] = df["start_station_id"].astype(str)
        _s = dim_stations.copy()
        _s["station_id"] = _s["station_id"].astype(str)
        df = df.merge(
            _s.rename(columns={
                "station_id":   "start_station_id",
                "station_name": "start_station_name",
                "latitude":     "start_lat",
                "longitude":    "start_lon",
            })[["city_id", "start_station_id", "start_station_name", "start_lat", "start_lon"]],
            on=["city_id", "start_station_id"], how="left",
        )

    # end station
    if not requested or requested.intersection({"end_station_name", "end_lat", "end_lon"}):
        if "dim_stations" not in locals():
            dim_stations = stations()
        df["end_station_id"] = df["end_station_id"].astype(str)
        _e = dim_stations.copy()
        _e["station_id"] = _e["station_id"].astype(str)
        df = df.merge(
            _e.rename(columns={
                "station_id":   "end_station_id",
                "station_name": "end_station_name",
                "latitude":     "end_lat",
                "longitude":    "end_lon",
            })[["city_id", "end_station_id", "end_station_name", "end_lat", "end_lon"]],
            on=["city_id", "end_station_id"], how="left",
        )

    # date dimension
    if (
        (not requested or requested.intersection({"date", "month", "month_name", "day_of_week", "day_name", "is_weekend", "quarter"}))
        and "date_id" in df.columns
    ):
        dim_date = dates()
        keep_cols = ["date_id","date","month","month_name",
                     "day_of_week","day_name","is_weekend","quarter"]
        keep_cols = [c for c in keep_cols if c in dim_date.columns]
        if keep_cols:
            df = df.merge(dim_date[keep_cols], on="date_id", how="left")

    if requested:
        ordered_columns = [column for column in required_columns or () if column in df.columns]
        result = df[ordered_columns]
        _emit_memory_debug(
            f"joined years={list(years)} city_ids={list(city_ids)} rows={len(result):,} cols={len(result.columns)} mem_mb={_dataframe_memory_mb(result):.2f} requested={ordered_columns}"
        )
        return result

    _emit_memory_debug(
        f"joined years={list(years)} city_ids={list(city_ids)} rows={len(df):,} cols={len(df.columns)} mem_mb={_dataframe_memory_mb(df):.2f} requested=all"
    )
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  Fluent query builder
# ══════════════════════════════════════════════════════════════════════════════

class GoldQuery:
    # Chainable filter builder for the gold layer.

    def __init__(self) -> None:
        self._city_names: list[str] = []
        self._years:      list[int] = []
        self._months:     list[int] = []

    # ── Filter methods ─────────────────────────────────────────────────────────

    def city(self, name: str) -> "GoldQuery":
        # Add a single city filter (case-insensitive).
        self._city_names.append(name)
        return self

    def cities(self, names: list[str]) -> "GoldQuery":
        # Add multiple cities at once.
        self._city_names.extend(names)
        return self

    def year(self, y: int) -> "GoldQuery":
        # Add a single year filter.
        self._years.append(y)
        return self

    def years(self, ys: list[int]) -> "GoldQuery":
        # Add multiple years at once.
        self._years.extend(ys)
        return self

    def month(self, m: int) -> "GoldQuery":
        # Add a single month filter (1-12).
        self._months.append(m)
        return self

    def months(self, ms: list[int]) -> "GoldQuery":
        # Add multiple months at once.
        self._months.extend(ms)
        return self

    # ── Terminal: execute the query ────────────────────────────────────────────

    def load(self, required_columns: list[str] | tuple[str, ...] | None = None) -> pd.DataFrame:
        # Execute the query and return a denormalised DataFrame.
        # Results are cached; empty DataFrame means no matching data.
        requested_columns = tuple(required_columns or ())
        internal_columns = list(requested_columns)
        if self._months and "month" not in internal_columns:
            internal_columns.append("month")

        # Resolve city_ids from names
        dim_city   = cities()
        target_ids: tuple[int, ...] = ()
        if self._city_names:
            lower = [c.lower() for c in self._city_names]
            ids   = dim_city[dim_city["city_name"].isin(lower)]["city_id"].tolist()
            target_ids = tuple(sorted(set(ids)))

        # Resolve years
        available  = available_years()
        if self._years:
            target_years = tuple(sorted(set(self._years) & set(available)))
        else:
            target_years = tuple(available)

        if not target_years:
            return pd.DataFrame()

        df = joined(
            city_ids=target_ids,
            years=target_years,
            required_columns=tuple(internal_columns) if internal_columns else None,
        )

        # Post-filter months (not worth caching at this granularity)
        if self._months and "month" in df.columns:
            df = df[df["month"].isin(self._months)]

        if requested_columns:
            keep_columns = [column for column in requested_columns if column in df.columns]
            df = df[keep_columns]

        _emit_memory_debug(
            f"query.load years={list(target_years)} city_ids={list(target_ids)} rows={len(df):,} cols={len(df.columns)} mem_mb={_dataframe_memory_mb(df):.2f} requested={list(requested_columns) or 'all'}"
        )

        return df.reset_index(drop=True)

    # ── Repr for debugging ─────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"GoldQuery(cities={self._city_names or 'all'}, "
            f"years={self._years or 'all'}, "
            f"months={self._months or 'all'})"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  Catalog — the single object page authors import
# ══════════════════════════════════════════════════════════════════════════════

class _GoldCatalog:
    # Gold layer catalog. Import `gold` from this module.

    # ── Raw dimension / fact tables ────────────────────────────────────────────

    def trips(self, years: list[int] = None) -> pd.DataFrame:
        # All fact trips, optionally filtered by year(s).
        # Returns the raw fact table without joined station/date columns.
        available = available_years()
        target    = tuple(sorted(set(years) & set(available))) if years else tuple(available)
        return facts(target)

    def stations(self) -> pd.DataFrame:
        # Dimension table of all bike stations with lat/lon.
        return stations()

    def dates(self) -> pd.DataFrame:
        # Calendar dimension table (date, year, month, weekday, etc.).
        return dates()

    def cities(self) -> pd.DataFrame:
        # City lookup table (city_id, city_name, display_name, country).
        return cities()

    def top_trip_patterns(
        self,
        city: str | None = None,
        years: list[int] | None = None,
        limit: int = 10,
    ) -> pd.DataFrame:
        # Precomputed top route patterns for map overlays.
        df = top_trip_patterns().copy()
        if df.empty:
            return df

        if city:
            city_lower = city.strip().lower()
            city_dim = cities()
            candidate_ids = city_dim[
                (city_dim["city_name"].str.lower() == city_lower)
                | (city_dim["display_name"].str.lower() == city_lower)
            ]["city_id"].tolist()
            if candidate_ids:
                df = df[df["city_id"].isin(candidate_ids)]
            else:
                return pd.DataFrame(columns=df.columns)

        if years and "year" in df.columns:
            year_set = set(int(y) for y in years)
            df = df[df["year"].isin(year_set)]

        if "rank" in df.columns:
            df = df[df["rank"] <= int(limit)]

        return df.reset_index(drop=True)

    # ── Fluent query builder ──────────────────────────────────────────────────

    def query(self) -> GoldQuery:
        # Start a fluent, chainable query against the gold layer.
        return GoldQuery()

    # ── One-liner convenience ──────────────────────────────────────────────────

    def for_city(
        self,
        city: str,
        year: int = None,
        years: list[int] = None,
    ) -> pd.DataFrame:
        # One-liner for fully joined trips for a city and optional year filters.
        q = self.query().city(city)
        if year is not None:
            q = q.year(year)
        if years is not None:
            q = q.years(years)
        return q.load()

    # ── Introspection ──────────────────────────────────────────────────────────

    def available_years(self) -> list[int]:
        # Return sorted years that have gold fact data.
        return available_years()

    def available_cities(self) -> list[str]:
        # Return city display names (e.g. Oslo, Bergen, Trondheim).
        return cities()["display_name"].tolist()

    def schema(self) -> None:
        # Print a column reference for the denormalised trips table.
        print("\n".join(_SCHEMA_REFERENCE_LINES))

    def status(self) -> dict:
        # Return summary dict: years available, city count, station count.
        return {
            "years":    self.available_years(),
            "cities":   self.available_cities(),
            "stations": len(self.stations()),
            "data_ok":  bool(self.available_years()),
        }


# ── Singleton — just import this ──────────────────────────────────────────────
gold = _GoldCatalog()
