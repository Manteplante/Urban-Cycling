import pandas as pd
import streamlit as st
from pathlib import Path

GOLD = Path(__file__).parents[2] / "02_data" / "03_gold"

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_gold_trips():
    return pd.read_csv(GOLD / "trips_summary.csv", parse_dates=['date'])

@st.cache_data(ttl=3600)
def load_gold_stations():
    return pd.read_csv(GOLD / "stations_master.csv")

@st.cache_data(ttl=3600)
def load_gold_hourly_patterns():
    return pd.read_csv(GOLD / "hourly_patterns.csv")