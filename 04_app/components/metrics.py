# KPI metric components for the Urban Cycling dashboard.

import streamlit as st
import pandas as pd
from services.gold import gold
from services.gcs_storage import gcs_runtime_status


# Four-column KPI row: trips, stations, avg duration, cities.
def headline_metrics(df: pd.DataFrame, n_cities_override: int | None = None) -> None:
    if df.empty:
        status = gcs_runtime_status()
        if not status["enabled"]:
            st.info("No data loaded: configure GOLD_GCS_BUCKET in Streamlit secrets for remote gold access.")
        elif not status["filesystem_ready"]:
            st.info("No data loaded: GCS credentials are missing or invalid in Streamlit secrets.")
        else:
            st.info("No data loaded for current filters from remote gold data.")
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
        status = gcs_runtime_status()
        if not status["enabled"]:
            st.warning("⚠️  No remote gold bucket configured. Set GOLD_GCS_BUCKET in Streamlit secrets.")
        elif not status["filesystem_ready"]:
            st.warning("⚠️  GCS authentication failed. Verify service-account secrets in Streamlit Cloud.")
        else:
            st.warning("⚠️  Remote gold data is reachable but no years were discovered in facts/fact_trips_*.csv.")

