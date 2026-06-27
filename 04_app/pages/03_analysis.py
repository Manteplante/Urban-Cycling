import streamlit as st
import plotly.express as px
from services.load_data import load_gold_trips

st.header("📈 Advanced Analytics")

trips = load_gold_trips()

# Sidebar filters specific to analysis
with st.sidebar.expander("Analysis Options"):
    analysis_type = st.selectbox("Analysis Type", 
        ["Hourly Patterns", "Day of Week", "Monthly Trends", "Seasonal"])
    
# Dynamic chart based on selection
if analysis_type == "Hourly Patterns":
    fig = px.line(trips.groupby('hour')['count'].sum(), 
                  title="Trips by Hour of Day")
    st.plotly_chart(fig, use_container_width=True)

# Download filtered data
st.download_button(
    label="Download Analysis Data",
    data=trips.to_csv(index=False),
    file_name="cycling_analysis.csv",
    mime="text/csv"
)