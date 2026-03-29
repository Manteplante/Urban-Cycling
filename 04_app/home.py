"""
Urban Cycling Analytics — Landing Page
Run from the 04_app/ directory:
    streamlit run home.py
"""

import pandas as pd
import streamlit as st

from components.metrics import headline_metrics, data_status_banner
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
    <h1 style='text-align:center; color:#FF6B6B; margin-bottom:0;'>🚲 Urban Cycling Analytics</h1>
    <p style='text-align:center; color:#666; font-size:1.05rem; margin-top:6px;'>
        Norwegian city bike-sharing data &mdash; Oslo · Bergen · Trondheim
    </p>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ── Data status ────────────────────────────────────────────────────────────────
data_status_banner()

# ── KPI metrics (latest available year) ───────────────────────────────────────
available_years = gold.available_years()
if available_years:
    latest_year = max(available_years)
    with st.spinner(f"Loading KPIs for {latest_year}…"):
        df_kpi = gold.query().years([latest_year]).load()
    headline_metrics(df_kpi)
    st.caption(f"KPIs for {latest_year} · use the sidebar on Maps / Temporal Patterns / Top Routes pages.")
else:
    headline_metrics(pd.DataFrame())

st.divider()

# ── City cards ─────────────────────────────────────────────────────────────────
st.subheader("Cities Covered")
cities = [
    ("🏙️ Oslo",       "Norway's capital and largest city",  "#FF6B6B", "Oslo Bysykkel"),
    ("🌊 Bergen",      "Gateway to the western fjords",      "#4ECDC4", "Bergen Bysykkel"),
    ("🏔️ Trondheim",  "Historic city of science & culture", "#FFD93D", "Trondheim Bysykkel"),
]
for col, (title, desc, colour, provider) in zip(st.columns(3), cities):
    with col:
        st.markdown(
            f"""
            <div style='border-left:4px solid {colour}; padding:14px 18px;
                        border-radius:4px; background:#fafafa; height:110px;'>
                <h3 style='margin:0; color:{colour};'>{title}</h3>
                <p style='margin:5px 0 2px; color:#333; font-size:.9rem;'>{desc}</p>
                <small style='color:#999;'>{provider}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── Navigation cards ───────────────────────────────────────────────────────────
st.subheader("Explore the Dashboard")
nav_col1, nav_col2, nav_col3 = st.columns(3)

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

with nav_col3:
    st.markdown(
        """
        <div style='border:1px solid #45B7D1; border-radius:8px; padding:20px; min-height:130px;'>
            <h3 style='color:#45B7D1;'>🔝 Top Routes & Stations</h3>
            <p style='color:#444;'>
                Inspect the busiest station-to-station corridors and the most
                used departure / arrival stations per city and year.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/04_top_routes_stations.py", label="Open Top Routes & Stations →")

st.divider()

# ── Getting started ────────────────────────────────────────────────────────────
with st.expander("ℹ️  Getting started — how to load your data"):
    st.markdown(
        """
        **1. Place raw CSVs into the data folder**
        ```
        02_data/raw/oslo/        ← CSV files from Oslo Bysykkel scraper
        02_data/raw/bergen/      ← Bergen
        02_data/raw/trondheim/   ← Trondheim
        ```
        The scraper in `01_scraper/` handles this automatically on each run.

        **2. Build the star schema**
        ```bash
        cd Urban-Cycling
        python 03_processing/transform.py
        ```
        This produces `02_data/processed/facts/` and `02_data/processed/dimensions/`.

        **3. Reload the app**
        Streamlit will pick up the new data on the next page interaction,
        or press **Clear Cache** in the sidebar.
        """
    )

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("**Urban Cycling Analytics**")
    st.markdown("---")
    st.markdown("📅 **Data range:** 2018 – 2025")
    st.markdown("🌍 **Source:** Oslo / Bergen / Trondheim Bysykkel open data")
    st.markdown("🔄 **Updated:** Monthly via automated scraper")
    st.markdown("---")
    if st.button("🗑️ Clear Cache"):
        st.cache_data.clear()
        st.success("Cache cleared!")
