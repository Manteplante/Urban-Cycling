# Work-trips route map (rush-hour windows).

# ── Imports ───────────────────────────────────────────────────────────────────
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from components.filters import default_year_selection
from services.notebook_outputs import load_export_df

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Work Trips - Urban Cycling",
    page_icon="🕘",
    layout="wide",
)
st.header("🕘 Work Trips")
st.caption("Top 10 distinct start-end routes for weekdays and rush-hour windows (06-09 and 14-17)")

REQUIRED_COLUMNS = [
    "city_name",
    "year",
    "day_of_week",
    "day_name",
    "time_bin",
    "duration_bin",
    "start_station_name",
    "start_lat",
    "start_lon",
    "end_station_name",
    "end_lat",
    "end_lon",
    "trips",
    "avg_duration_minutes",
    "median_duration_minutes",
]

# ── Load and validate export contract ─────────────────────────────────────────
routes = load_export_df("work_trips_routes.csv", required_columns=REQUIRED_COLUMNS)

if routes.empty:
    st.info(
        "Work-trip exports are missing. Run "
        "03_processing/workspace/03_work_trips.ipynb to create them."
    )
    st.stop()

required = set(REQUIRED_COLUMNS)
missing = sorted(required - set(routes.columns))
if missing:
    st.error("Work-trip export has missing columns: " + ", ".join(missing))
    st.stop()

# ── Type cleanup and weekday scope ────────────────────────────────────────────
routes["year"] = pd.to_numeric(routes["year"], errors="coerce")
routes["day_of_week"] = pd.to_numeric(routes["day_of_week"], errors="coerce")
routes["trips"] = pd.to_numeric(routes["trips"], errors="coerce")
routes = routes.dropna(subset=["year", "day_of_week", "trips", "day_name"]).copy()
routes["year"] = routes["year"].astype(int)
routes["day_of_week"] = routes["day_of_week"].astype(int)
routes["trips"] = routes["trips"].astype(int)

for column in [
    "city_name",
    "day_name",
    "time_bin",
    "duration_bin",
    "start_station_name",
    "end_station_name",
]:
    routes[column] = routes[column].astype("category")

# Enforce weekday-only scope for this chapter.
routes = routes[routes["day_of_week"].between(0, 4)].copy()

# Keep only distinct corridors.
routes = routes[
    routes["start_station_name"].astype(str).str.strip().str.lower()
    != routes["end_station_name"].astype(str).str.strip().str.lower()
].copy()

if routes.empty:
    st.info("No distinct start-end work-trip routes available.")
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
all_cities = sorted(routes["city_name"].dropna().unique().tolist())
all_years = sorted(routes["year"].dropna().unique().tolist())
time_bin_order = ["Morning (06-09)", "Evening (14-17)"]
time_bins_available = [b for b in time_bin_order if b in set(routes["time_bin"].dropna().unique())]
duration_bin_order = [
    "0-5 min",
    "6-10 min",
    "11-15 min",
    "16-20 min",
    "21-25 min",
    "25-30 min",
    "30+ min",
]
duration_bins_available = [b for b in duration_bin_order if b in set(routes["duration_bin"].dropna().unique())]
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
weekday_options = [d for d in weekday_order if d in set(routes["day_name"].dropna().unique())]

with st.sidebar:
    st.markdown("### 🕘 Work-trip filters")
    selected_city = st.selectbox("City", options=["All Cities"] + all_cities, index=0)
    selected_years = st.multiselect("Year", options=all_years, default=default_year_selection(all_years))
    selected_weekdays = st.multiselect("Day of week", options=weekday_options, default=weekday_options)
    selected_time_bins = st.multiselect("Time bin", options=time_bins_available, default=time_bins_available)
    selected_duration_bins = st.multiselect(
        "Duration bin",
        options=duration_bins_available,
        default=duration_bins_available,
    )

if not selected_years:
    st.warning("Select at least one year.")
    st.stop()
if not selected_time_bins:
    st.warning("Select at least one time bin.")
    st.stop()
if not selected_duration_bins:
    st.warning("Select at least one duration bin.")
    st.stop()
if not selected_weekdays:
    st.warning("Select at least one weekday.")
    st.stop()

# ── Filter and build top-route summary ────────────────────────────────────────
mask = routes["year"].isin(selected_years)
mask &= routes["day_name"].isin(selected_weekdays)
mask &= routes["time_bin"].isin(selected_time_bins)
mask &= routes["duration_bin"].isin(selected_duration_bins)
if selected_city != "All Cities":
    mask &= routes["city_name"] == selected_city

plot_df = routes.loc[mask].copy()

if plot_df.empty:
    st.info("No work-trip routes found for the selected filters.")
    st.stop()

summary = (
    plot_df.groupby(
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
        trips=("trips", "sum"),
        avg_duration_minutes=("avg_duration_minutes", "mean"),
        median_duration_minutes=("median_duration_minutes", "mean"),
    )
    .sort_values("trips", ascending=False)
    .head(10)
    .reset_index(drop=True)
)

if summary.empty:
    st.info("No top routes available for the selected filters.")
    st.stop()

summary["rank"] = summary.index + 1
summary["avg_duration_minutes"] = summary["avg_duration_minutes"].round(2)
summary["median_duration_minutes"] = summary["median_duration_minutes"].round(2)
summary["route_label"] = summary.apply(
    lambda r: (
        f"{r['city_name']} | #{int(r['rank'])} "
        f"{r['start_station_name']} -> {r['end_station_name']} ({int(r['trips']):,} trips)"
    ),
    axis=1,
)

# ── Route selection for map display ───────────────────────────────────────────
with st.sidebar:
    route_options = summary["route_label"].tolist()
    selected_routes = st.multiselect(
        "Top 10 routes",
        options=route_options,
        default=route_options,
        help="Top 10 routes are selected by default.",
    )

if not selected_routes:
    st.warning("Select at least one route to display.")
    st.stop()

# ── Render map + overlays ─────────────────────────────────────────────────────
selected = pd.DataFrame()
selected = summary[summary["route_label"].isin(selected_routes)].sort_values("rank").reset_index(drop=True)

all_lats = pd.concat([selected["start_lat"], selected["end_lat"]], ignore_index=True)
all_lons = pd.concat([selected["start_lon"], selected["end_lon"]], ignore_index=True)
m = folium.Map(location=[all_lats.mean(), all_lons.mean()], zoom_start=12, tiles="CartoDB Positron")

line_colors = [
    "#1f78b4", "#33a02c", "#e31a1c", "#ff7f00", "#6a3d9a",
    "#a6cee3", "#b2df8a", "#fb9a99", "#fdbf6f", "#cab2d6",
]

for idx, row in selected.iterrows():
    line_color = line_colors[idx % len(line_colors)]

    folium.PolyLine(
        locations=[[row["start_lat"], row["start_lon"]], [row["end_lat"], row["end_lon"]]],
        color=line_color,
        weight=5,
        opacity=0.85,
        tooltip=row["route_label"],
        popup=folium.Popup(
            (
                f"<b>{row['route_label']}</b><br>"
                f"City: {row['city_name']}<br>"
                f"Avg duration: {row['avg_duration_minutes']:.1f} min<br>"
                f"Median duration: {row['median_duration_minutes']:.1f} min"
            ),
            max_width=360,
        ),
    ).add_to(m)

    folium.CircleMarker(
        location=[row["start_lat"], row["start_lon"]],
        radius=7,
        color="white",
        fill=True,
        fill_color="#2ca25f",
        fill_opacity=0.9,
        weight=1.2,
        tooltip=f"Start #{int(row['rank'])}: {row['start_station_name']}",
    ).add_to(m)

    folium.CircleMarker(
        location=[row["end_lat"], row["end_lon"]],
        radius=7,
        color="white",
        fill=True,
        fill_color="#d73027",
        fill_opacity=0.9,
        weight=1.2,
        tooltip=f"End #{int(row['rank'])}: {row['end_station_name']}",
    ).add_to(m)

m.fit_bounds(
    [
        [all_lats.min(), all_lons.min()],
        [all_lats.max(), all_lons.max()],
    ],
    padding=(16, 16),
)

c1, c2, c3 = st.columns(3)
c1.metric("Filtered route rows", f"{len(plot_df):,}")
c2.metric("Top routes shown", f"{len(selected):,}")
c3.metric("Trips in selected routes", f"{int(selected['trips'].sum()):,}")

st_folium(m, width=980, height=560, returned_objects=[])

# ── Optional detail table ─────────────────────────────────────────────────────
with st.expander("Selected route details"):
    st.dataframe(
        selected[
            [
                "rank",
                "city_name",
                "start_station_name",
                "end_station_name",
                "trips",
                "avg_duration_minutes",
                "median_duration_minutes",
            ]
        ],
        width="stretch",
        hide_index=True,
    )
