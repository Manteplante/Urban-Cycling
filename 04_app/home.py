"""
Urban Cycling Analytics — Landing Page
Run from the 04_app/ directory:
    streamlit run home.py
"""

import pandas as pd
import streamlit as st
from pathlib import Path

from components.metrics import headline_metrics
from services.gold import gold

st.set_page_config(
    page_title="Urban Cycling — Norwegian Bike Analytics",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style='text-align:center; color:#FF6B6B; margin-bottom:0;'>🚲 Bysykkel - Oslo, Bergen, Trondheim</h1>
    <p style='text-align:center; color:#666; font-size:1.05rem; margin-top:6px;'>
        Norwegian city bike-sharing data &mdash; Oslo · Bergen · Trondheim
    </p>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ── Frontpage photo ───────────────────────────────────────────────────────────
app_dir = Path(__file__).resolve().parent
frontpage_photo = app_dir / "photos" / "frontpage" / "frontpage-photo.png"

photo_col_left, photo_col_main, photo_col_right = st.columns([1, 12, 1])
if frontpage_photo.exists():
    with photo_col_main:
        st.image(str(frontpage_photo), width=1040)
else:
    with photo_col_main:
        st.markdown(
            """
            <div style='width:1040px; max-width:100%; min-height:693px; border:2px dashed #D9D9D9;
                        border-radius:10px; padding:28px; text-align:center; background:#FCFCFC;
                        color:#666; display:flex; align-items:center; justify-content:center;
                        flex-direction:column; box-sizing:border-box;'>
                <h4 style='margin:0 0 8px;'>Frontpage image placeholder</h4>
                <p style='margin:0;'>Add your PNG as <strong>frontpage-photo.png</strong> in:</p>
                <p style='margin:4px 0 0; font-family:monospace;'>04_app/photos/frontpage/</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── KPI metrics (latest available year) ───────────────────────────────────────
available_years = gold.available_years()
all_cities = gold.available_cities()
if available_years:
    latest_year = max(available_years)
    with st.spinner(f"Loading KPIs for {latest_year}…"):
        df_kpi = gold.query().years([latest_year]).load()
    headline_metrics(df_kpi, n_cities_override=len(all_cities) if all_cities else None)
    st.markdown(
        f"""
        <div style='margin-top:10px; border:2px solid #FF6B6B; background:#FFF1F1;
                    border-radius:10px; padding:10px 14px; text-align:center;'>
            <span style='font-size:1.1rem; font-weight:800; color:#B30021; letter-spacing:.4px;'>
                SNAPSHOT FOR {latest_year}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    headline_metrics(pd.DataFrame())

st.divider()

# ── City cards ─────────────────────────────────────────────────────────────────
st.subheader("Cities Covered")
cities = [
    (
        "🏙️ Oslo",
        "Norway's capital and largest city",
        "#FF6B6B",
        "Oslo Bysykkel",
        "https://no.wikipedia.org/wiki/Oslo",
        "https://sykkelnorge.no/artikler/gronne-sykkelturer-oslo",
    ),
    (
        "🌊 Bergen",
        "Gateway to the western fjords",
        "#4ECDC4",
        "Bergen Bysykkel",
        "https://no.wikipedia.org/wiki/Bergen",
        "https://sykkelnorge.no/artikler/gronne-sykkelruter-bergen",
    ),
    (
        "🏔️ Trondheim",
        "Historic city of science & culture",
        "#FFD93D",
        "Trondheim Bysykkel",
        "https://no.wikipedia.org/wiki/Trondheim",
        "https://miljopakken.no/sykkelkart",
    ),
]
for col, (title, desc, colour, provider, wiki_url, extra_url) in zip(st.columns(3), cities):
    with col:
        st.markdown(
            f"""
            <div style='border-left:4px solid {colour}; padding:14px 18px;
                        border-radius:4px; background:#fafafa; min-height:160px;'>
                <h3 style='margin:0; color:{colour};'>{title}</h3>
                <p style='margin:5px 0 2px; color:#333; font-size:.9rem;'>{desc}</p>
                <p style='margin:0 0 6px; font-size:.85rem;'>
                    <a href='{wiki_url}' target='_blank'>Wikipedia</a>
                </p>
                <p style='margin:0 0 6px; font-size:.85rem;'>
                    <a href='{extra_url}' target='_blank'>Bike routes</a>
                </p>
                <small style='color:#999;'>{provider}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── Navigation cards ───────────────────────────────────────────────────────────
st.subheader("Content")
st.caption("Choose a chapter to explore")
nav_col1, nav_col2 = st.columns(2)

with nav_col1:
    st.markdown(
        """
        <div style='border:1px solid #FF6B6B; border-radius:8px; padding:20px; min-height:130px;'>
            <h3 style='color:#FF6B6B;'>🗺️ Maps</h3>
            <p style='color:#444;'>
                Interactive station maps showing where trips start and end.
                Station bubbles are sized and coloured by trip volume so the
                busiest hubs stand out instantly.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/02_maps.py", label="Open Maps →")

    st.markdown(
        """
        <div style='border:1px solid #45B7D1; border-radius:8px; padding:20px; min-height:130px; margin-top:10px;'>
            <h3 style='color:#45B7D1;'>🔝 Top Routes & Stations</h3>
            <p style='color:#444;'>
                Inspect the busiest station-to-station corridors and the most
                used departure and arrival stations per city and year.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/04_top_routes_stations.py", label="Open Top Routes & Stations →")

    st.markdown(
        """
        <div style='border:1px solid #F29E4C; border-radius:8px; padding:20px; min-height:130px; margin-top:10px;'>
            <h3 style='color:#F29E4C;'>📅 Yearly Trends</h3>
            <p style='color:#444;'>
                Compare total trip volumes year by year across Oslo, Bergen,
                and Trondheim.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/06_yearly_trends.py", label="Open Yearly Trends →")

with nav_col2:
    st.markdown(
        """
        <div style='border:1px solid #4ECDC4; border-radius:8px; padding:20px; min-height:130px;'>
            <h3 style='color:#4ECDC4;'>⏱️ Temporal Patterns</h3>
            <p style='color:#444;'>
                Explore when people ride with hourly, weekday, and monthly
                demand profiles across selected cities and years.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/03_temporal_patterns.py", label="Open Temporal Patterns →")
    st.page_link("pages/03_work_trips.py", label="Open Work Trips →")

    st.markdown(
        """
        <div style='border:1px solid #7A77B9; border-radius:8px; padding:20px; min-height:130px; margin-top:10px;'>
            <h3 style='color:#7A77B9;'>🍂 Seasonal Variations</h3>
            <p style='color:#444;'>
                Compare winter versus summer demand and how seasonal behavior
                differs between cities.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/05_seasonal_variations.py", label="Open Seasonal Variations →")

    st.markdown(
        """
        <div style='border:1px solid #2F6F9F; border-radius:8px; padding:20px; min-height:130px; margin-top:10px;'>
            <h3 style='color:#2F6F9F;'>🧭 Longest Trips View</h3>
            <p style='color:#444;'>
                Select the top longest trip routes and inspect the start-end
                corridor directly on the map.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/07_longest_trips_view.py", label="Open Longest Trips View →")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Chapters")
    st.page_link("pages/02_maps.py", label="🗺️ Maps")
    st.page_link("pages/03_temporal_patterns.py", label="⏱️ Temporal Patterns")
    st.page_link("pages/03_work_trips.py", label="🕘 Work Trips")
    st.page_link("pages/04_top_routes_stations.py", label="🔝 Top Routes & Stations")
    st.page_link("pages/05_seasonal_variations.py", label="🍂 Seasonal Variations")
    st.page_link("pages/06_yearly_trends.py", label="📅 Yearly Trends")
    st.page_link("pages/07_longest_trips_view.py", label="🧭 Longest Trips View")
