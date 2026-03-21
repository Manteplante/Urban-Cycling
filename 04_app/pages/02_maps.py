"""Maps page — interactive station map for the selected city/year."""

import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium

from components.filters import sidebar_filters
from services.transform import station_trip_counts

st.set_page_config(
    page_title="Maps — Urban Cycling",
    page_icon="🗺️",
    layout="wide",
)
st.header("🗺️ Bike Station Map")

# ── Filters ────────────────────────────────────────────────────────────────────
query = sidebar_filters(key_prefix="maps")

with st.sidebar:
    colour_by = st.radio(
        "Colour stations by",
        options=["total_trips", "departures", "arrivals"],
        format_func=lambda x: x.replace("_", " ").title(),
        index=0,
    )

# ── Load data ──────────────────────────────────────────────────────────────────
with st.spinner("Loading trip data…"):
    df = query.load()

if df.empty:
    st.info(
        "No data found for the selected filters. "
        "Make sure you have run: `python 03_processing/transform.py`"
    )
    st.stop()

stations_df = station_trip_counts(df)

if stations_df.empty:
    st.warning("Could not compute station metrics from the loaded data.")
    st.stop()

# ── Summary row ────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Trips",         f"{len(df):,}")
c2.metric("Stations on map",     f"{len(stations_df):,}")
c3.metric("Busiest station",     stations_df.iloc[0]["station_name"] if not stations_df.empty else "—")
c4.metric("Avg trips / station", f"{int(stations_df['total_trips'].mean()):,}")

st.divider()

# ── Build Folium map ───────────────────────────────────────────────────────────
center_lat = stations_df["latitude"].mean()
center_lon = stations_df["longitude"].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=13,
    tiles="CartoDB Positron",
)

max_val = stations_df[colour_by].max() or 1

for _, row in stations_df.iterrows():
    if pd.isna(row["latitude"]) or pd.isna(row["longitude"]):
        continue

    intensity = row[colour_by] / max_val
    radius    = 5 + intensity * 18

    # Green → yellow → red gradient
    r_val  = int(min(255, intensity * 2 * 255))
    g_val  = int(min(255, (1 - intensity) * 2 * 255))
    colour = f"#{r_val:02x}{g_val:02x}50"

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=radius,
        popup=folium.Popup(
            f"<b>{row['station_name']}</b><br>"
            f"Departures: {int(row['departures']):,}<br>"
            f"Arrivals:   {int(row['arrivals']):,}<br>"
            f"Total:      {int(row['total_trips']):,}",
            max_width=220,
        ),
        tooltip=f"{row['station_name']} ({int(row[colour_by]):,})",
        color="white",
        fill=True,
        fill_color=colour,
        fill_opacity=0.85,
        weight=1.5,
    ).add_to(m)

st_folium(m, width=900, height=560, returned_objects=[])

st.divider()

# ── Top stations table ─────────────────────────────────────────────────────────
st.subheader("Top 15 Stations")
top = (
    stations_df.head(15)[["station_name", "departures", "arrivals", "total_trips"]]
    .copy()
    .rename(columns={
        "station_name": "Station",
        "departures":   "Departures",
        "arrivals":     "Arrivals",
        "total_trips":  "Total Trips",
    })
)
st.dataframe(top, use_container_width=True, hide_index=True)
