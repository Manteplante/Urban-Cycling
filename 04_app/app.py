import streamlit as st

st.set_page_config(
    page_title="Urban Cycling Analytics",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Urban Cycling Analytics Dashboard")
st.markdown("**Real-time insights from Oslo, Bergen, and Trondheim bike-sharing data**")

# Sidebar filters (global across pages)
with st.sidebar:
    st.header("Filters")
    city = st.multiselect("Select Cities", ["Oslo", "Bergen", "Trondheim"], default=["Oslo"])
    date_range = st.date_input("Date Range", [])
    st.info("Data updated monthly via automated scraper")