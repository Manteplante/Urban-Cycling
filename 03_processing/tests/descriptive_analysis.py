# descriptive_analysis.py
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def run_descriptive_analysis():
    file_path = r"C:\Users\matia\Desktop\report\step1\OSLO\2024_mai.csv"
    data = pd.read_csv(file_path)
    
    st.subheader("Data Overview")
    st.write("First 10 rows:")
    st.write(data.head(10))
    st.write("Data Types:")
    st.write(data.dtypes)

    # Grouping and visualizing the data
    trip_counts = data.groupby(['start_station_name', 'end_station_name']).size().reset_index(name='Count')
    top_5_trips = trip_counts.sort_values(by='Count', ascending=False).head(5)
    
    st.subheader("Top 5 Trips")
    st.write(top_5_trips)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    labels = [f"{row['start_station_name']} -> {row['end_station_name']} ({row['Count']})" for _, row in top_5_trips.iterrows()]
    ax.barh(labels, top_5_trips['Count'])
    ax.set_xlabel('Antall bysykkel-turer')
    ax.set_ylabel('Tur (Start -> Stopp)')
    ax.set_title('Topp fem Oslo Bysykkel-turer i Juli 2024')
    ax.invert_yaxis()
    st.pyplot(fig)