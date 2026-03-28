"""
services/gold.py — Urban Cycling Gold Layer Catalog
═══════════════════════════════════════════════════════════════════════════════

This is the single import point for all gold layer data in the Streamlit app.
Think of it like connecting a Power BI report to a semantic model — you pick
the table or query you need, all caching and joins are handled for you.

──────────────────────────────────────────────────────────────────────────────
QUICK START  (in any page or component)
──────────────────────────────────────────────────────────────────────────────

    from services.gold import gold

    # 1. Raw tables — just like picking a table in Power BI
    df_trips    = gold.trips()          # all fact_trips (all years)
    df_stations = gold.stations()       # dim_stations with lat/lon
    df_dates    = gold.dates()          # dim_date calendar table
    df_cities   = gold.cities()         # dim_city lookup

    # 2. Fluent filtering — chain as many filters as you like
    df = (
        gold.query()
            .city("Oslo")              # one city
            .cities(["Oslo","Bergen"]) # or multiple
            .year(2024)                # one year
            .years([2023, 2024])       # or multiple
            .month(7)                  # optional month filter
            .load()                    # → fully joined, denormalised DataFrame
    )

    # 3. Convenience one-liners
    df = gold.for_city("Oslo", year=2024)

    # 4. Schema reference — see what columns come back
    gold.schema()         # prints column names + dtypes for trips

──────────────────────────────────────────────────────────────────────────────
COLUMN REFERENCE  (returned by .load() and for_city())
──────────────────────────────────────────────────────────────────────────────
    trip_id                 int
    city_name               str    "Oslo" | "Bergen" | "Trondheim"
    start_station_id        str
    start_station_name      str
    start_lat / start_lon   float
    end_station_id          str
    end_station_name        str
    end_lat / end_lon       float
    date_id                 int    YYYYMMDD
    date                    date
    year                    int
    month                   int    1–12
    month_name              str    "January" … "December"
    day_of_week             int    0=Mon … 6=Sun
    day_name                str    "Monday" … "Sunday"
    is_weekend              int    0 | 1
    quarter                 int    1–4
    start_hour              int    0–23
    duration_seconds        float
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Optional

# ── Paths ──────────────────────────────────────────────────────────────────────
_PROJECT_ROOT    = Path(__file__).parents[2]
_GOLD_PATH       = _PROJECT_ROOT / "02_data" / "gold"
_FACTS_PATH      = _GOLD_PATH / "facts"
_DIMENSIONS_PATH = _GOLD_PATH / "dimensions"


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
    """Fully denormalised trips table, filtered and joined once, then cached."""
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
    """Chainable filter builder for the gold layer.

    Usage::

        df = gold.query().city("Oslo").year(2024).load()
    """

    def __init__(self) -> None:
        self._city_names: list[str] = []
        self._years:      list[int] = []
        self._months:     list[int] = []

    # ── Filter methods ─────────────────────────────────────────────────────────

    def city(self, name: str) -> "GoldQuery":
        """Add a single city filter (case-insensitive)."""
        self._city_names.append(name)
        return self

    def cities(self, names: list[str]) -> "GoldQuery":
        """Add multiple cities at once."""
        self._city_names.extend(names)
        return self

    def year(self, y: int) -> "GoldQuery":
        """Add a single year filter."""
        self._years.append(y)
        return self

    def years(self, ys: list[int]) -> "GoldQuery":
        """Add multiple years at once."""
        self._years.extend(ys)
        return self

    def month(self, m: int) -> "GoldQuery":
        """Add a single month filter (1–12)."""
        self._months.append(m)
        return self

    def months(self, ms: list[int]) -> "GoldQuery":
        """Add multiple months at once."""
        self._months.extend(ms)
        return self

    # ── Terminal: execute the query ────────────────────────────────────────────

    def load(self) -> pd.DataFrame:
        """Execute the query and return a denormalised DataFrame.

        All joins are handled automatically and results are cached.
        Returns an empty DataFrame if no data is found — safe to check
        with ``df.empty``."""
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
    """The gold layer catalog.  Import ``gold`` from this module.

    Think of this as the semantic model in Power BI — all the tables are here,
    cleaned, joined, and cached.  You never touch file paths or ETL logic.
    """

    # ── Raw dimension / fact tables ────────────────────────────────────────────

    def trips(self, years: list[int] = None) -> pd.DataFrame:
        """All fact trips, optionally filtered by year(s).

        Returns the raw fact table (no station names or dates joined).
        Use ``.query().load()`` if you need the full denormalised view.
        """
        available = _available_years()
        target    = tuple(sorted(set(years) & set(available))) if years else tuple(available)
        return _facts(target)

    def stations(self) -> pd.DataFrame:
        """Dimension table of all bike stations with lat/lon."""
        return _stations()

    def dates(self) -> pd.DataFrame:
        """Calendar dimension table (date, year, month, weekday, etc.)."""
        return _dates()

    def cities(self) -> pd.DataFrame:
        """City lookup table (city_id, city_name, display_name, country)."""
        return _cities()

    def top_trip_patterns(
        self,
        city: str | None = None,
        years: list[int] | None = None,
        limit: int = 10,
    ) -> pd.DataFrame:
        """Precomputed top route patterns for map overlays."""
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
        """Start a fluent, chainable query against the gold layer.

        Example::

            df = gold.query().city("Oslo").year(2024).load()
        """
        return GoldQuery()

    # ── One-liner convenience ──────────────────────────────────────────────────

    def for_city(
        self,
        city: str,
        year: int = None,
        years: list[int] = None,
    ) -> pd.DataFrame:
        """One-liner: load fully joined trips for a city (and optionally year/years).

        Examples::

            df = gold.for_city("Oslo")
            df = gold.for_city("Oslo", year=2024)
            df = gold.for_city("Bergen", years=[2023, 2024])
        """
        q = self.query().city(city)
        if year is not None:
            q = q.year(year)
        if years is not None:
            q = q.years(years)
        return q.load()

    # ── Introspection ──────────────────────────────────────────────────────────

    def available_years(self) -> list[int]:
        """Return a sorted list of years that have gold fact data."""
        return _available_years()

    def available_cities(self) -> list[str]:
        """Return a list of city display names (e.g. ['Oslo', 'Bergen', 'Trondheim'])."""
        return _cities()["display_name"].tolist()

    def schema(self) -> None:
        """Print the column reference for the denormalised trips table."""
        print(__doc__.split("COLUMN REFERENCE")[1].split("═")[0].strip())

    def status(self) -> dict:
        """Return a summary dict: years available, city count, station count."""
        return {
            "years":    self.available_years(),
            "cities":   self.available_cities(),
            "stations": len(self.stations()),
            "data_ok":  bool(self.available_years()),
        }


# ── Singleton — just import this ──────────────────────────────────────────────
gold = _GoldCatalog()
