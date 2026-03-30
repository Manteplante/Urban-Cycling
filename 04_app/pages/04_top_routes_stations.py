"""Top routes and stations page driven by notebook exports."""

import pandas as pd
import plotly.express as px
import streamlit as st

from components.filters import default_year_selection
from services.notebook_outputs import load_export_df

st.set_page_config(
    page_title="Top Routes and Stations - Urban Cycling",
    page_icon="🔝",
    layout="wide",
)
st.header("🔝 Top Routes and Stations")

routes = load_export_df("top_routes_city_year.csv")
stations = load_export_df("top_stations_city_year.csv")

if routes.empty or stations.empty:
    st.info(
        "Top routes/stations exports are missing. Run "
        "03_processing/workspace/05_top_routes_stations.ipynb to create them."
    )
    st.stop()

required_routes = {
    "city_name",
    "year",
    "start_station_name",
    "end_station_name",
    "trips",
}
required_stations = {
    "city_name",
    "year",
    "station_name",
    "departures",
    "arrivals",
    "total_trips",
}

missing_routes = sorted(required_routes - set(routes.columns))
missing_stations = sorted(required_stations - set(stations.columns))
if missing_routes or missing_stations:
    details = []
    if missing_routes:
        details.append(f"routes: {', '.join(missing_routes)}")
    if missing_stations:
        details.append(f"stations: {', '.join(missing_stations)}")
    st.error("Top exports have missing columns - " + " | ".join(details))
    st.stop()

routes["year"] = pd.to_numeric(routes["year"], errors="coerce")
stations["year"] = pd.to_numeric(stations["year"], errors="coerce")
routes = routes.dropna(subset=["year", "city_name", "start_station_name", "end_station_name", "trips"]).copy()
stations = stations.dropna(subset=["year", "city_name", "station_name", "total_trips"]).copy()
routes["year"] = routes["year"].astype(int)
stations["year"] = stations["year"].astype(int)

all_cities = sorted(set(routes["city_name"]) | set(stations["city_name"]))
all_years = sorted(set(routes["year"]) | set(stations["year"]))

with st.sidebar:
    st.markdown("### 🔝 Routes and stations filters")
    selected_city = st.selectbox("City", options=["All Cities"] + all_cities, index=0)
    selected_years = st.multiselect("Year", options=all_years, default=default_year_selection(all_years))
    top_n = st.slider("Top N", min_value=5, max_value=30, value=10, step=1)

if not selected_years:
    st.warning("Select at least one year to display charts.")
    st.stop()

if selected_city == "All Cities":
    routes_plot = routes[routes["year"].isin(selected_years)].copy()
    stations_plot = stations[stations["year"].isin(selected_years)].copy()
else:
    routes_plot = routes[(routes["year"].isin(selected_years)) & (routes["city_name"] == selected_city)].copy()
    stations_plot = stations[(stations["year"].isin(selected_years)) & (stations["city_name"] == selected_city)].copy()

if routes_plot.empty or stations_plot.empty:
    st.info("No top route/station data found for the selected filters.")
    st.stop()

routes_plot["route"] = routes_plot["start_station_name"] + " -> " + routes_plot["end_station_name"]
routes_view = (
    routes_plot.groupby("route", as_index=False)["trips"].sum().sort_values("trips", ascending=False).head(top_n)
)
start_stations_view = (
    stations_plot[stations_plot["departures"] > 0]
    .groupby("station_name", as_index=False)["departures"]
    .sum()
    .sort_values("departures", ascending=False)
    .head(top_n)
)
end_stations_view = (
    stations_plot[stations_plot["arrivals"] > 0]
    .groupby("station_name", as_index=False)["arrivals"]
    .sum()
    .sort_values("arrivals", ascending=False)
    .head(top_n)
)

col_a, col_b, col_c = st.columns(3)
col_a.metric("Route rows", f"{len(routes_plot):,}")
col_b.metric("Station rows", f"{len(stations_plot):,}")
col_c.metric("Unique stations", f"{stations_plot['station_name'].nunique():,}")

fig_routes = px.bar(
    routes_view.sort_values("trips", ascending=True),
    x="trips",
    y="route",
    orientation="h",
    title=f"Top {top_n} Routes",
    labels={"trips": "Trips", "route": "Route"},
    color="trips",
    color_continuous_scale="Oranges",
)
fig_routes.update_layout(showlegend=False, coloraxis_showscale=False, plot_bgcolor="white")
st.plotly_chart(fig_routes, use_container_width=True)

start_col, end_col = st.columns(2)

with start_col:
    fig_start_stations = px.bar(
        start_stations_view.sort_values("departures", ascending=True),
        x="departures",
        y="station_name",
        orientation="h",
        title=f"Top {top_n} Start Stations",
        labels={"departures": "Departures", "station_name": "Start station"},
        color="departures",
        color_continuous_scale="Tealgrn",
    )
    fig_start_stations.update_layout(showlegend=False, coloraxis_showscale=False, plot_bgcolor="white")
    st.plotly_chart(fig_start_stations, use_container_width=True)

with end_col:
    fig_end_stations = px.bar(
        end_stations_view.sort_values("arrivals", ascending=True),
        x="arrivals",
        y="station_name",
        orientation="h",
        title=f"Top {top_n} End Stations",
        labels={"arrivals": "Arrivals", "station_name": "End station"},
        color="arrivals",
        color_continuous_scale="Blues",
    )
    fig_end_stations.update_layout(showlegend=False, coloraxis_showscale=False, plot_bgcolor="white")
    st.plotly_chart(fig_end_stations, use_container_width=True)

with st.expander("Show detail tables"):
    st.markdown("**Routes**")
    st.dataframe(routes_view, use_container_width=True, hide_index=True)
    st.markdown("**Start stations**")
    st.dataframe(start_stations_view, use_container_width=True, hide_index=True)
    st.markdown("**End stations**")
    st.dataframe(end_stations_view, use_container_width=True, hide_index=True)
