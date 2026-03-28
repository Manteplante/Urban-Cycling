"""Trip durations page — histogram-only view."""

import streamlit as st

from components.charts import histogram_duration
from services.gold import gold

st.set_page_config(
    page_title="Trip Durations — Urban Cycling",
    page_icon="⏱️",
    layout="wide",
)
st.header("⏱️ Trip Durations")

with st.sidebar:
    st.markdown("### ⏱️ Duration filters")
    cities = gold.available_cities() or ["Oslo", "Bergen", "Trondheim"]
    selected_city = st.selectbox("City", options=["All Cities"] + cities, index=0)
    years = gold.available_years()
    selected_years = st.multiselect("Year", options=years, default=years)
    cutoff = st.slider("Histogram cutoff (minutes)", 10, 120, 60, key="trip_duration_cutoff")

# Dynamic histogram (same logic as 03_analysis.py)
hist_query = gold.query()
if selected_city != "All Cities":
    hist_query = hist_query.city(selected_city)
if selected_years:
    hist_query = hist_query.years(selected_years)
hist_df = hist_query.load()

st.subheader("Trip Duration Distribution")
if hist_df.empty:
    st.info("No trip-level data found for histogram with the selected filters.")
else:
    st.plotly_chart(histogram_duration(hist_df, max_minutes=cutoff), use_container_width=True)
