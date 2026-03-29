"""
Urban Cycling Analytics — Landing Page
Run from the 04_app/ directory:
    streamlit run home.py
"""

import pandas as pd
import streamlit as st

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
    <h1 style='text-align:center; color:#FF6B6B; margin-bottom:0;'>🚲 Urban Cycling Analytics</h1>
    <p style='text-align:center; color:#666; font-size:1.05rem; margin-top:6px;'>
        Norwegian city bike-sharing data &mdash; Oslo · Bergen · Trondheim
    </p>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ── KPI metrics (latest available year) ───────────────────────────────────────
available_years = gold.available_years()
if available_years:
    latest_year = max(available_years)
    with st.spinner(f"Loading KPIs for {latest_year}…"):
        df_kpi = gold.query().years([latest_year]).load()
    headline_metrics(df_kpi)
    st.caption(f"Snapshot for {latest_year}")
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

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Chapters")
    st.page_link("pages/02_maps.py", label="🗺️ Maps")
    st.page_link("pages/03_temporal_patterns.py", label="⏱️ Temporal Patterns")
    st.page_link("pages/04_top_routes_stations.py", label="🔝 Top Routes & Stations")
    st.page_link("pages/05_seasonal_variations.py", label="🍂 Seasonal Variations")
    st.page_link("pages/06_yearly_trends.py", label="📅 Yearly Trends")
