# Longest duration trips route view — map focused on >30 minute start→end corridors.

# ── Imports ───────────────────────────────────────────────────────────────────
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from components.filters import default_year_selection
from services.gold import gold

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Longest Duration-Trips View — Urban Cycling",
    page_icon="🧭",
    layout="wide",
)
st.header("🧭 Longest Duration-Trips View")
st.caption("Route-focused map for trips longer than 30 minutes")

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧭 Long-trip filters")
    all_cities = gold.available_cities() or ["Oslo", "Bergen", "Trondheim"]
    selected_city = st.selectbox("City", options=["All Cities"] + all_cities, index=0)

    all_years = gold.available_years()
    selected_years = st.multiselect("Year", options=all_years, default=default_year_selection(all_years))

if not selected_years:
    st.warning("Select at least one year to display long trips.")
    st.stop()

# ── Load and validate gold data ───────────────────────────────────────────────
query = gold.query().years(selected_years)
if selected_city != "All Cities":
    query = query.city(selected_city)

with st.spinner("Loading long-trip data…"):
    df = query.load()

if df.empty:
    st.info("No data found for the selected filters.")
    st.stop()

required = [
    "trip_id",
    "city_name",
    "duration_seconds",
    "start_station_name",
    "start_lat",
    "start_lon",
    "end_station_name",
    "end_lat",
    "end_lon",
]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.stop()

# ── Derive long-trip route summaries ──────────────────────────────────────────
long_trips = df.dropna(subset=["duration_seconds"]).copy()
long_trips["duration_minutes"] = long_trips["duration_seconds"] / 60
long_trips = long_trips[long_trips["duration_minutes"] > 30].copy()

long_trips = long_trips.dropna(
    subset=[
        "city_name",
        "start_station_name",
        "start_lat",
        "start_lon",
        "end_station_name",
        "end_lat",
        "end_lon",
    ]
)

if long_trips.empty:
    st.info("No trips above 30 minutes found for the selected filters.")
    st.stop()

route_summary = (
    long_trips.groupby(
        [
            "city_name",
            "start_station_name",
            "start_lat",
            "start_lon",
            "end_station_name",
            "end_lat",
            "end_lon",
        ],
        as_index=False,
    )
    .agg(
        long_trips=("trip_id", "count"),
        avg_duration_minutes=("duration_minutes", "mean"),
        median_duration_minutes=("duration_minutes", "median"),
    )
    .sort_values("long_trips", ascending=False)
    .reset_index(drop=True)
)

# Keep only distinct start→end corridors (exclude loops where start == end).
route_summary = route_summary[
    route_summary["start_station_name"].astype(str).str.strip().str.lower()
    != route_summary["end_station_name"].astype(str).str.strip().str.lower()
].reset_index(drop=True)

if route_summary.empty:
    st.info("No long-trip routes with distinct start and end stations for the selected filters.")
    st.stop()

route_summary["rank"] = route_summary.index + 1
route_summary["avg_duration_minutes"] = route_summary["avg_duration_minutes"].round(2)
route_summary["median_duration_minutes"] = route_summary["median_duration_minutes"].round(2)
route_summary["route_label"] = route_summary.apply(
    lambda r: (
        f"#{int(r['rank'])} {r['start_station_name']} -> {r['end_station_name']} "
        f"({int(r['long_trips']):,} long trips)"
    ),
    axis=1,
)

# ── Build station-level diagnostics used in popups ────────────────────────────
start_summary = (
    long_trips.groupby(["city_name", "start_station_name", "start_lat", "start_lon"], as_index=False)
    .agg(
        departures=("trip_id", "count"),
        departure_duration_sum=("duration_minutes", "sum"),
    )
    .rename(
        columns={
            "start_station_name": "station_name",
            "start_lat": "latitude",
            "start_lon": "longitude",
        }
    )
)
end_summary = (
    long_trips.groupby(["city_name", "end_station_name", "end_lat", "end_lon"], as_index=False)
    .agg(
        arrivals=("trip_id", "count"),
        arrival_duration_sum=("duration_minutes", "sum"),
    )
    .rename(
        columns={
            "end_station_name": "station_name",
            "end_lat": "latitude",
            "end_lon": "longitude",
        }
    )
)
station_summary = start_summary.merge(
    end_summary,
    on=["city_name", "station_name", "latitude", "longitude"],
    how="outer",
)

for col in ["departures", "arrivals", "departure_duration_sum", "arrival_duration_sum"]:
    station_summary[col] = station_summary[col].fillna(0)
station_summary["departures"] = station_summary["departures"].astype(int)
station_summary["arrivals"] = station_summary["arrivals"].astype(int)
station_summary["total_long_trips"] = station_summary["departures"] + station_summary["arrivals"]
station_summary["duration_sum"] = station_summary["departure_duration_sum"] + station_summary["arrival_duration_sum"]
station_summary["avg_duration_minutes"] = (station_summary["duration_sum"] / station_summary["total_long_trips"]).round(2)

station_summary["key"] = (
    station_summary["city_name"].astype(str)
    + "|"
    + station_summary["station_name"].astype(str)
    + "|"
    + station_summary["latitude"].astype(str)
    + "|"
    + station_summary["longitude"].astype(str)
)
station_lookup = station_summary.set_index("key")

# ── Route selector ────────────────────────────────────────────────────────────
with st.sidebar:
    route_options = route_summary["route_label"].head(10).tolist()
    selected_routes = st.multiselect(
        "Longest routes (top 10)",
        options=route_options,
        default=route_options,
        help="Showing top 10 longest routes by default.",
    )

if not selected_routes:
    st.warning("Select at least one route to display on the map.")
    st.stop()

selected_route_df = (
    route_summary[route_summary["route_label"].isin(selected_routes)]
    .sort_values("rank")
    .reset_index(drop=True)
)


# ── Station popup helper ──────────────────────────────────────────────────────
def station_stats(city_name: str, station_name: str, lat: float, lon: float) -> dict:
    key = f"{city_name}|{station_name}|{lat}|{lon}"
    if key not in station_lookup.index:
        return {"departures": 0, "arrivals": 0, "total_long_trips": 0, "avg_duration_minutes": 0.0}
    row = station_lookup.loc[key]
    return {
        "departures": int(row["departures"]),
        "arrivals": int(row["arrivals"]),
        "total_long_trips": int(row["total_long_trips"]),
        "avg_duration_minutes": float(row["avg_duration_minutes"]),
    }

# ── Render map and overlays ───────────────────────────────────────────────────
all_lats = pd.concat([selected_route_df["start_lat"], selected_route_df["end_lat"]], ignore_index=True)
all_lons = pd.concat([selected_route_df["start_lon"], selected_route_df["end_lon"]], ignore_index=True)
center_lat = all_lats.mean()
center_lon = all_lons.mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB Positron")

line_colors = [
    "#1f78b4", "#33a02c", "#e31a1c", "#ff7f00", "#6a3d9a",
    "#a6cee3", "#b2df8a", "#fb9a99", "#fdbf6f", "#cab2d6",
]

for idx, route_row in selected_route_df.iterrows():
    line_color = line_colors[idx % len(line_colors)]
    start_stats = station_stats(
        route_row["city_name"], route_row["start_station_name"], route_row["start_lat"], route_row["start_lon"]
    )
    end_stats = station_stats(
        route_row["city_name"], route_row["end_station_name"], route_row["end_lat"], route_row["end_lon"]
    )

    folium.PolyLine(
        locations=[[route_row["start_lat"], route_row["start_lon"]], [route_row["end_lat"], route_row["end_lon"]]],
        color=line_color,
        weight=5,
        opacity=0.85,
        tooltip=f"{route_row['route_label']}",
        popup=folium.Popup(
            f"<b>{route_row['route_label']}</b><br>City: {route_row['city_name']}<br>Avg duration: {route_row['avg_duration_minutes']:.1f} min<br>Median duration: {route_row['median_duration_minutes']:.1f} min",
            max_width=360,
        ),
    ).add_to(m)

    folium.CircleMarker(
        location=[route_row["start_lat"], route_row["start_lon"]],
        radius=7,
        color="white",
        fill=True,
        fill_color="#2ca25f",
        fill_opacity=0.9,
        weight=1.2,
        tooltip=f"Start #{int(route_row['rank'])}: {route_row['start_station_name']}",
        popup=folium.Popup(
            f"<b>Start: {route_row['start_station_name']}</b><br>Route: #{int(route_row['rank'])}<br>City: {route_row['city_name']}<br>Total long trips: {start_stats['total_long_trips']:,}<br>Departures: {start_stats['departures']:,}<br>Arrivals: {start_stats['arrivals']:,}<br>Avg duration: {start_stats['avg_duration_minutes']:.1f} min",
            max_width=320,
        ),
    ).add_to(m)

    folium.CircleMarker(
        location=[route_row["end_lat"], route_row["end_lon"]],
        radius=7,
        color="white",
        fill=True,
        fill_color="#d73027",
        fill_opacity=0.9,
        weight=1.2,
        tooltip=f"End #{int(route_row['rank'])}: {route_row['end_station_name']}",
        popup=folium.Popup(
            f"<b>End: {route_row['end_station_name']}</b><br>Route: #{int(route_row['rank'])}<br>City: {route_row['city_name']}<br>Total long trips: {end_stats['total_long_trips']:,}<br>Departures: {end_stats['departures']:,}<br>Arrivals: {end_stats['arrivals']:,}<br>Avg duration: {end_stats['avg_duration_minutes']:.1f} min",
            max_width=320,
        ),
    ).add_to(m)

m.fit_bounds(
    [
        [all_lats.min(), all_lons.min()],
        [all_lats.max(), all_lons.max()],
    ],
    padding=(16, 16),
)

c1, c2, c3 = st.columns(3)
c1.metric("Long trips (>30 min)", f"{len(long_trips):,}")
c2.metric("Routes", f"{len(route_summary):,}")
c3.metric("Selected route trips", f"{int(selected_route_df['long_trips'].sum()):,}")

st_folium(m, width=980, height=560, returned_objects=[])

# ── Optional detail tables ────────────────────────────────────────────────────
with st.expander("Selected route details"):
    st.dataframe(
        selected_route_df[[
            "rank",
            "city_name",
            "start_station_name",
            "end_station_name",
            "long_trips",
            "avg_duration_minutes",
            "median_duration_minutes",
        ]],
        width="stretch",
        hide_index=True,
    )

with st.expander("Top 20 long-trip routes"):
    st.dataframe(
        route_summary[[
            "rank",
            "city_name",
            "start_station_name",
            "end_station_name",
            "long_trips",
            "avg_duration_minutes",
            "median_duration_minutes",
        ]].head(20),
        width="stretch",
        hide_index=True,
    )
