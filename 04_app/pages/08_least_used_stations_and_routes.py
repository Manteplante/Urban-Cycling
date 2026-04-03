# Least-used stations and routes map page.

# ── Imports ───────────────────────────────────────────────────────────────────
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from components.filters import default_year_selection
from services.notebook_outputs import load_export_df

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Least Used Stations and Routes - Urban Cycling",
    page_icon="📉",
    layout="wide",
)
st.header("📉 Least Used Stations and Routes")
st.caption("Station-dot map of least-used stations, with trip bins and yearly filters.")


# ── Map helper ────────────────────────────────────────────────────────────────
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


# ── Export fallback builder ───────────────────────────────────────────────────
def build_station_table_from_role_exports() -> pd.DataFrame:
    starts = load_export_df("least_used_start_stations.csv")
    ends = load_export_df("least_used_end_stations.csv")
    if starts.empty and ends.empty:
        return pd.DataFrame()

    if not starts.empty:
        starts = starts.rename(
            columns={
                "trips": "departures",
                "lat": "latitude",
                "lon": "longitude",
            }
        )
    if not ends.empty:
        ends = ends.rename(
            columns={
                "trips": "arrivals",
                "lat": "latitude",
                "lon": "longitude",
            }
        )

    keep_start = [
        c for c in [
            "city_name",
            "year",
            "station_name",
            "latitude",
            "longitude",
            "departures",
        ] if c in starts.columns
    ]
    keep_end = [
        c for c in [
            "city_name",
            "year",
            "station_name",
            "latitude",
            "longitude",
            "arrivals",
        ] if c in ends.columns
    ]

    starts = starts[keep_start] if not starts.empty else pd.DataFrame(columns=keep_start)
    ends = ends[keep_end] if not ends.empty else pd.DataFrame(columns=keep_end)

    merged = starts.merge(
        ends,
        on=["city_name", "year", "station_name", "latitude", "longitude"],
        how="outer",
    )

    for col in ["departures", "arrivals"]:
        if col not in merged.columns:
            merged[col] = 0
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0)

    merged["total_trips"] = merged["departures"] + merged["arrivals"]

    bin_edges = [0, 500, 1000, 2000, 3000, 4000, 5000, 6000]
    bin_labels = ["1-500", "501-1000", "1001-2000", "2001-3000", "3001-4000", "4001-5000", "5001-6000"]
    merged["trip_bin"] = pd.cut(
        merged["total_trips"],
        bins=bin_edges,
        labels=bin_labels,
        include_lowest=True,
        right=True,
    ).astype(str)

    return merged


# ── Load and validate station export ──────────────────────────────────────────
stations = load_export_df("least_used_stations.csv")
if stations.empty:
    stations = build_station_table_from_role_exports()

if stations.empty:
    st.info(
        "Least-used station exports are missing. Run "
        "03_processing/workspace/07_least_used_stations.ipynb to create them."
    )
    st.stop()

required = {
    "city_name",
    "year",
    "station_name",
    "latitude",
    "longitude",
    "departures",
    "arrivals",
    "total_trips",
    "trip_bin",
}
missing = sorted(required - set(stations.columns))
if missing:
    st.error("Least-used station export has missing columns: " + ", ".join(missing))
    st.stop()

# ── Type cleanup ──────────────────────────────────────────────────────────────
for col in [
    "year",
    "departures",
    "arrivals",
    "total_trips",
]:
    if col in stations.columns:
        stations[col] = pd.to_numeric(stations[col], errors="coerce")

stations = stations.dropna(
    subset=[
        "city_name",
        "year",
        "station_name",
        "latitude",
        "longitude",
        "departures",
        "arrivals",
        "total_trips",
        "trip_bin",
    ]
).copy()

stations["year"] = stations["year"].astype(int)
stations["departures"] = stations["departures"].astype(int)
stations["arrivals"] = stations["arrivals"].astype(int)
stations["total_trips"] = stations["total_trips"].astype(int)
stations["trip_bin"] = stations["trip_bin"].astype(str)

if stations.empty:
    st.info("No least-used stations available in export.")
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
all_cities = sorted(stations["city_name"].dropna().unique().tolist())
all_years = sorted(stations["year"].dropna().unique().tolist())
bin_order = [
    "1-500",
    "501-1000",
    "1001-2000",
    "2001-3000",
    "3001-4000",
    "4001-5000",
    "5001-6000",
]
bin_options = [b for b in bin_order if b in set(stations["trip_bin"].dropna().unique())]

with st.sidebar:
    st.markdown("### 📉 Least-used filters")
    city_options = ["All Cities"] + all_cities
    default_city_index = city_options.index("Oslo") if "Oslo" in city_options else 0
    selected_city = st.selectbox("City", options=city_options, index=default_city_index)
    selected_years = st.multiselect("Year", options=all_years, default=default_year_selection(all_years))
    selected_bins = st.multiselect("Trip bin", options=bin_options, default=bin_options)
    bottom_n = st.slider("Least-used stations to show", min_value=5, max_value=100, value=10, step=1)
    colour_by = st.radio(
        "Colour stations by",
        options=["total_trips", "departures", "arrivals"],
        format_func=lambda x: x.replace("_", " ").title(),
        index=0,
    )

if not selected_years:
    st.warning("Select at least one year.")
    st.stop()
if not selected_bins:
    st.warning("Select at least one trip bin.")
    st.stop()

plot_df = stations[stations["year"].isin(selected_years)].copy()
plot_df = plot_df[plot_df["trip_bin"].isin(selected_bins)].copy()
if selected_city != "All Cities":
    plot_df = plot_df[plot_df["city_name"] == selected_city].copy()

if plot_df.empty:
    st.info("No least-used stations found for the selected filters.")
    st.stop()

# ── Build least-used view ─────────────────────────────────────────────────────
summary = (
    plot_df.sort_values(["total_trips", "city_name", "year"], ascending=[True, True, True])
    .head(bottom_n)
    .reset_index(drop=True)
)
summary["rank"] = summary.index + 1

c1, c2, c3, c4 = st.columns(4)
c1.metric("Filtered station rows", f"{len(plot_df):,}")
c2.metric("Stations shown", f"{len(summary):,}")
c3.metric("Least-used station", summary.iloc[0]["station_name"] if not summary.empty else "—")
c4.metric("Avg trips / station", f"{int(round(summary['total_trips'].mean())):,}")

st.divider()

# ── Render map ────────────────────────────────────────────────────────────────
center_lat = summary["latitude"].mean()
center_lon = summary["longitude"].mean()
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11 if selected_city != "All Cities" else 6,
    tiles="CartoDB Positron",
)

fit_bounds(m, summary[["latitude", "longitude"]])

max_val = summary[colour_by].max() or 1
for _, row in summary.iterrows():
    intensity = float(row[colour_by]) / float(max_val)
    radius = 5 + intensity * 18

    r_val = int(min(255, intensity * 2 * 255))
    g_val = int(min(255, (1 - intensity) * 2 * 255))
    colour = f"#{r_val:02x}{g_val:02x}50"

    trips_display = int(row["total_trips"])

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=radius,
        popup=folium.Popup(
            f"<b>{row['station_name']}</b><br>"
            f"City/Year: {row['city_name']} {int(row['year'])}<br>"
            f"Departures: {int(row['departures']):,}<br>"
            f"Arrivals: {int(row['arrivals']):,}<br>"
            f"Total trips: {trips_display:,}<br>"
            f"Trip bin: {row['trip_bin']}",
            max_width=260,
        ),
        tooltip=f"#{int(row['rank'])} {row['station_name']} ({trips_display:,})",
        color="white",
        fill=True,
        fill_color=colour,
        fill_opacity=0.85,
        weight=1.5,
    ).add_to(m)

st_folium(m, width=900, height=560, returned_objects=[])

st.divider()
# ── Optional table ────────────────────────────────────────────────────────────
with st.expander("Selected station details"):
    st.dataframe(
        summary[
            [
                "rank",
                "city_name",
                "year",
                "station_name",
                "trip_bin",
                "departures",
                "arrivals",
                "total_trips",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
