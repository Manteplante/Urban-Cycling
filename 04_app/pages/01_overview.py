import streamlit as st
from services.load_data import load_gold_trips, load_gold_stations
from components.metrics import show_kpis
from components.charts import trips_over_time, popular_stations

st.header("📊 Overview")

# Load gold layer data
trips_df = load_gold_trips()
stations_df = load_gold_stations()

# Display KPIs in columns
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Trips", f"{trips_df['total_trips'].sum():,}", delta="+12%")
with col2:
    st.metric("Avg Duration", f"{trips_df['avg_duration'].mean():.1f} min")
with col3:
    st.metric("Active Stations", len(stations_df))
with col4:
    st.metric("Cities Covered", 3)

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["Trends", "Top Stations", "City Comparison"])

with tab1:
    st.plotly_chart(trips_over_time(trips_df), use_container_width=True)
    
with tab2:
    st.dataframe(popular_stations(stations_df), use_container_width=True)
    
with tab3:
    st.bar_chart(trips_df.groupby('city')['total_trips'].sum())