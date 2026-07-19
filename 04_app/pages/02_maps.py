# Maps page — interactive station map with city zoom and route overlays.

# ── Imports ───────────────────────────────────────────────────────────────────
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from components.filters import sidebar_filters
from services.gold import gold
from services.gcs_storage import gcs_runtime_status
from services.transform import (
    route_slicer_options,
    selected_route_lines,
    station_trip_counts,
)

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Maps — Urban Cycling",
    page_icon="🗺️",
    layout="wide",
)
st.header("🗺️ Bike Station Map")

# ── Filters ────────────────────────────────────────────────────────────────────
query = sidebar_filters(
    key_prefix="maps",
    include_city=False,
)


def fit_bounds(map_obj: folium.Map, points: pd.DataFrame) -> None:
    if points.empty:
        return
    min_lat = points["latitude"].min()
    max_lat = points["latitude"].max()
    min_lon = points["longitude"].min()
    max_lon = points["longitude"].max()
    if pd.isna(min_lat) or pd.isna(max_lat) or pd.isna(min_lon) or pd.isna(max_lon):
        return
    map_obj.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]], padding=(16, 16))


def route_weight(route_row: pd.Series, max_trips: int) -> float:
    if max_trips <= 0:
        return 3.0
    return 2.5 + (float(route_row["trip_count"]) / float(max_trips)) * 5.0

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧭 Map view")
    all_city_options = ["All Cities"] + (gold.available_cities() or ["Oslo", "Bergen", "Trondheim"])
    city_view_state = st.selectbox(
        "City zoom",
        options=all_city_options,
        index=all_city_options.index("Oslo") if "Oslo" in all_city_options else 0,
        key="maps_city_view",
    )

    colour_by = st.radio(
        "Colour stations by",
        options=["total_trips", "departures", "arrivals"],
        format_func=lambda x: x.replace("_", " ").title(),
        index=0,
    )

    show_routes = st.checkbox("Overlay top route patterns", value=True, key="maps_show_routes")

# ── Load data ──────────────────────────────────────────────────────────────────
with st.spinner("Loading trip data…"):
    df = query.load()

if df.empty:
    status = gcs_runtime_status()
    if not status["enabled"]:
        st.error("No data source configured. Set GOLD_GCS_BUCKET in Streamlit secrets.")
    elif not status["filesystem_ready"]:
        st.error("GCS authentication failed. Check Streamlit secrets for service-account credentials.")
    else:
        st.info(
            "No data found for the selected filters in remote gold data. "
            "Try widening city/year/month filters or verify fact_trips files in your configured bucket/prefix."
        )
    st.stop()

selected_city = city_view_state

map_df = df if selected_city == "All Cities" else df[df["city_name"] == selected_city].copy()

if map_df.empty and selected_city != "All Cities":
    st.warning(
        f"No data for {selected_city} with current year/month filters. "
        "Try adding more years in the sidebar."
    )
    st.stop()

stations_df = station_trip_counts(map_df)

if stations_df.empty:
    st.warning("Could not compute station metrics from the loaded data.")
    st.stop()

# ── Summary row ────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Trips",         f"{len(map_df):,}")
c2.metric("Stations on map",     f"{len(stations_df):,}")
c3.metric("Busiest station",     stations_df.iloc[0]["station_name"] if not stations_df.empty else "—")
c4.metric("Avg trips / station", f"{int(stations_df['total_trips'].mean()):,}")

st.divider()

# ── Build Folium map ───────────────────────────────────────────────────────────
center_lat = stations_df["latitude"].mean()
center_lon = stations_df["longitude"].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11 if selected_city != "All Cities" else 6,
    tiles="CartoDB Positron",
)

fit_bounds(m, stations_df[["latitude", "longitude"]])

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

# ── Optional route overlay ─────────────────────────────────────────────────────
route_lines = pd.DataFrame()
if show_routes and selected_city != "All Cities":
    years = sorted(map_df["year"].dropna().astype(int).unique().tolist()) if "year" in map_df.columns else []
    patterns = gold.top_trip_patterns(city=selected_city, years=years, limit=10)

    if patterns.empty:
        st.info("No top route patterns found in gold facts for this city/year selection yet.")
    else:
        patterns = route_slicer_options(patterns)
        with st.sidebar:
            route_labels = patterns["route_label"].tolist()
            selected_labels = st.multiselect(
                "Top trip patterns",
                options=route_labels,
                default=route_labels[:1],
                key="maps_selected_routes",
            )

        label_to_key = dict(zip(patterns["route_label"], patterns["route_key"]))
        selected_keys = [label_to_key[label] for label in selected_labels if label in label_to_key]
        route_lines = selected_route_lines(patterns, selected_keys)

if not route_lines.empty:
    max_route_trips = int(route_lines["trip_count"].max()) if "trip_count" in route_lines.columns else 1
    for _, route in route_lines.iterrows():
        popup = folium.Popup(
            f"<b>#{int(route['rank'])} {route['start_station_name']} → {route['end_station_name']}</b><br>"
            f"Trips: {int(route['trip_count']):,}<br>"
            f"Avg duration: {float(route['avg_duration_seconds']) / 60:.1f} min<br>"
            f"Median duration: {float(route['median_duration_seconds']) / 60:.1f} min",
            max_width=320,
        )
        folium.PolyLine(
            locations=[
                [route["start_lat"], route["start_lon"]],
                [route["end_lat"], route["end_lon"]],
            ],
            color="#1f78b4",
            weight=route_weight(route, max_route_trips),
            opacity=0.8,
            tooltip=route.get("route_label", "Route"),
            popup=popup,
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
st.dataframe(top, width="stretch", hide_index=True)
