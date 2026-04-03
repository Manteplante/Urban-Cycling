# KPI metric components for the Urban Cycling dashboard.

import streamlit as st
import pandas as pd
from services.gold import gold


# Four-column KPI row: trips, stations, avg duration, cities.
def headline_metrics(df: pd.DataFrame, n_cities_override: int | None = None) -> None:
    if df.empty:
        st.info(
            "No data loaded yet. "
            "Add raw CSVs to `02_data/raw/{city}/` then run: "
            "`python 03_processing/transform.py`"
        )
        return

    total_trips  = len(df)
    n_stations   = df["start_station_name"].nunique() if "start_station_name" in df.columns else 0
    n_cities     = df["city_name"].nunique()           if "city_name"          in df.columns else 0
    if n_cities_override is not None:
        n_cities = int(n_cities_override)
    avg_duration = (
        round(df["duration_seconds"].dropna().mean() / 60, 1)
        if "duration_seconds" in df.columns else None
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Trips",     f"{total_trips:,}")
    c2.metric("Unique Stations", f"{n_stations:,}")
    c3.metric("Avg Duration",    f"{avg_duration} min" if avg_duration is not None else "—")
    c4.metric("Cities",          n_cities)


# Green success bar when data is present, yellow warning when missing.
def data_status_banner() -> None:
    years = gold.available_years()
    if years:
        st.success(f"✅  Gold layer loaded — years available: {', '.join(str(y) for y in years)}")
    else:
        st.warning(
            "⚠️  No processed data found.  "
            "Place raw CSVs in `02_data/raw/{{city}}/` then run `python 03_processing/transform.py`."
        )

