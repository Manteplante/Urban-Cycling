import streamlit as st
import pydeck as pdk
from services.load_data import load_gold_stations

st.header("🗺️ Interactive Maps")

stations = load_gold_stations()

# Station map with pydeck
st.subheader("Station Locations")
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
        latitude=59.9,
        longitude=10.75,
        zoom=11,
        pitch=50,
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=stations,
            get_position='[lon, lat]',
            get_color='[200, 30, 0, 160]',
            get_radius=100,
        ),
    ],
))

# Heatmap
st.subheader("Trip Density Heatmap")
st.map(stations[['lat', 'lon']])