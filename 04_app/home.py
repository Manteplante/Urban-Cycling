import streamlit as st

st.title("Urban Cycling Analytics Dashboard")
st.markdown("**Real-time insights from Oslo, Bergen, and Trondheim bike-sharing data**")

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Cities Covered", 3)
    st.write("🏙️ Oslo, Bergen, Trondheim")

with col2:
    st.metric("Data Period", "2018-2024")
    st.write("📅 Multi-year historical data")

with col3:
    st.metric("Data Source", "Automated")
    st.write("🤖 Monthly updates via scraper")

st.divider()

st.subheader("📊 Dashboard Pages")

col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/02_maps.py", label="📍 Maps", icon="🗺️")
    st.write("Interactive maps of bike-sharing stations")

with col2:
    st.page_link("pages/03_analysis.py", label="📈 Analysis", icon="📈")
    st.write("Detailed statistical analysis and insights")

st.divider()

st.info("💡 Use the filters in the sidebar to customize your view across all pages")

# Sidebar filters (global across pages)
with st.sidebar:
    st.header("Filters")
    city = st.multiselect("Select Cities", ["Oslo", "Bergen", "Trondheim"], default=["Oslo"])
    date_range = st.date_input("Date Range", [])
    st.divider()
    st.info("Data updated monthly via automated scraper")