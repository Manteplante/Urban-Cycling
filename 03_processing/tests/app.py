#### Basic template ####
# app.py
#  to run app --> streamlit run app.py

# Importing Libraries
import streamlit as st
import pandas as pd
import numpy as np


# Import modules from other files in the project
from descriptive_analysis import run_descriptive_analysis
from linear_regression import run_linear_regression
from introduction import run_introduction


# Title of the app
st.title("Norwegian Bike Sharing Data")

# Introduction
st.markdown("Welcome to the Norwegian City Bike Sharing Data Analysis App")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Choose a page", ["Introduction", "Descriptive Analysis", "Linear Regression", "Map Visualization"])

# Page router function (loop)
if page == "Introduction":
    run_introduction()

elif page == "Descriptive Analysis":
    st.header("Descriptive Analysis")
    st.write("This page is about the descriptive analysis of the data.")
    run_descriptive_analysis()

elif page == "Linear Regression":
    st.header("Linear Regression")
    st.write("This page is about the linear regression analysis of the data.")
    run_linear_regression()

elif page == "Map Visualization":
    st.header("Map Visualization")
    # Use folium to integrate the map
    st.map(data) # Placeholder: replace with actual geospatial data and mapping logic
