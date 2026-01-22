import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.header("📊 Overview")

# Display cities map
st.subheader("📍 Cities Covered")
cities_data = pd.DataFrame({
    'lat': [59.9139, 60.3913, 63.4305],
    'lon': [10.7522, 5.3221, 10.3951],
    'city': ['Oslo', 'Bergen', 'Trondheim'],
})

# Create Folium map centered on Norway
m = folium.Map(
    location=[61.5, 8.5],
    zoom_start=5,
    tiles="CartoDB Positron"
)

# Add markers for each city
for idx, row in cities_data.iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=15,
        popup=row['city'],
        tooltip=row['city'],
        color='white',
        fill=True,
        fillColor='#FF6B6B',
        fillOpacity=0.8,
        weight=2
    ).add_to(m)

# Display the map
st_folium(m, width=700, height=500)