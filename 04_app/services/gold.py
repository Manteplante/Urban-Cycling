# services/gold.py — Urban Cycling Gold Layer Catalog
# Single import point for gold-layer access in the Streamlit app.
# Use gold.query() for joined data, or gold.{trips,stations,dates,cities}()
# for direct table access.

from __future__ import annotations

import os
import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# ── Paths ──────────────────────────────────────────────────────────────────────
_PROJECT_ROOT    = Path(__file__).parents[2]
load_dotenv(_PROJECT_ROOT / ".env")


def _resolve_env_path(var_name: str, default_relative: str) -> Path:
    raw = (os.getenv(var_name) or default_relative).strip()
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = _PROJECT_ROOT / candidate
    return candidate.resolve()


_GOLD_PATH       = _resolve_env_path("GOLD_PATH", "02_data/gold")
_FACTS_PATH      = _resolve_env_path("FACTS_PATH", "02_data/gold/facts")
_DIMENSIONS_PATH = _resolve_env_path("DIMENSIONS_PATH", "02_data/gold/dimensions")

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

@st.cache_data(ttl=3600)
def _cities() -> pd.DataFrame:
    path = _DIMENSIONS_PATH / "dim_city.csv"
    if not path.exists():
        return pd.DataFrame({
            "city_id":      [1,       2,         3],
            "city_name":    ["oslo",  "bergen",  "trondheim"],
            "display_name": ["Oslo",  "Bergen",  "Trondheim"],
            "country":      ["Norway","Norway",  "Norway"],
        })
    return pd.read_csv(path)


@st.cache_data(ttl=3600)
def _stations() -> pd.DataFrame:
    path = _DIMENSIONS_PATH / "dim_stations.csv"
    if not path.exists():
        return pd.DataFrame(columns=["station_id","station_name","latitude","longitude","city_id"])
    return pd.read_csv(path)


@st.cache_data(ttl=3600)
def _dates() -> pd.DataFrame:
    path = _DIMENSIONS_PATH / "dim_date.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=["date"])


@st.cache_data(ttl=3600)
def _available_years() -> list[int]:
    if not _FACTS_PATH.exists():
        return []
    return sorted(
        int(f.stem.split("_")[-1])
        for f in _FACTS_PATH.glob("fact_trips_*.csv")
    )


@st.cache_data(ttl=3600)
def _facts(years: tuple[int, ...]) -> pd.DataFrame:
    if not _FACTS_PATH.exists():
        return pd.DataFrame()
    frames = []
    for yr in years:
        p = _FACTS_PATH / f"fact_trips_{yr}.csv"
        if p.exists():
            df = pd.read_csv(p)
            df["year"] = yr
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@st.cache_data(ttl=3600)
def _top_trip_patterns() -> pd.DataFrame:
    path = _FACTS_PATH / "fact_top_trip_patterns.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=3600)
def _joined(city_ids: tuple[int, ...], years: tuple[int, ...]) -> pd.DataFrame:
    # Fully denormalised trips table, filtered and joined once, then cached.
    facts = _facts(years)
    if facts.empty:
        return pd.DataFrame()

    if city_ids:
        facts = facts[facts["city_id"].isin(city_ids)]
    if facts.empty:
        return pd.DataFrame()

    dim_city     = _cities()
    dim_stations = _stations()
    dim_date     = _dates()

    df = facts.copy()

    # city name
    df = df.merge(
        dim_city[["city_id","display_name"]].rename(columns={"display_name": "city_name"}),
        on="city_id", how="left",
    )

    # start station
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
    if not dim_date.empty and "date_id" in df.columns:
        keep_cols = ["date_id","date","month","month_name",
                     "day_of_week","day_name","is_weekend","quarter"]
        keep_cols = [c for c in keep_cols if c in dim_date.columns]
        df = df.merge(dim_date[keep_cols], on="date_id", how="left")

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

    def load(self) -> pd.DataFrame:
        # Execute the query and return a denormalised DataFrame.
        # Results are cached; empty DataFrame means no matching data.
        # Resolve city_ids from names
        dim_city   = _cities()
        target_ids: tuple[int, ...] = ()
        if self._city_names:
            lower = [c.lower() for c in self._city_names]
            ids   = dim_city[dim_city["city_name"].isin(lower)]["city_id"].tolist()
            target_ids = tuple(sorted(set(ids)))

        # Resolve years
        available  = _available_years()
        if self._years:
            target_years = tuple(sorted(set(self._years) & set(available)))
        else:
            target_years = tuple(available)

        if not target_years:
            return pd.DataFrame()

        df = _joined(city_ids=target_ids, years=target_years)

        # Post-filter months (not worth caching at this granularity)
        if self._months and "month" in df.columns:
            df = df[df["month"].isin(self._months)]

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
        available = _available_years()
        target    = tuple(sorted(set(years) & set(available))) if years else tuple(available)
        return _facts(target)

    def stations(self) -> pd.DataFrame:
        # Dimension table of all bike stations with lat/lon.
        return _stations()

    def dates(self) -> pd.DataFrame:
        # Calendar dimension table (date, year, month, weekday, etc.).
        return _dates()

    def cities(self) -> pd.DataFrame:
        # City lookup table (city_id, city_name, display_name, country).
        return _cities()

    def top_trip_patterns(
        self,
        city: str | None = None,
        years: list[int] | None = None,
        limit: int = 10,
    ) -> pd.DataFrame:
        # Precomputed top route patterns for map overlays.
        df = _top_trip_patterns().copy()
        if df.empty:
            return df

        if city:
            city_lower = city.strip().lower()
            city_dim = _cities()
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
        return _available_years()

    def available_cities(self) -> list[str]:
        # Return city display names (e.g. Oslo, Bergen, Trondheim).
        return _cities()["display_name"].tolist()

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
