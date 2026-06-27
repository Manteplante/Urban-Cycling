# introduction.py
import streamlit as st
from PIL import Image

def run_introduction():
    st.header("Introduction")
    st.write("This app is a dashboard that can be used to analyze the Norwegian Bike Sharing Data.")
    
    # Load and display an image. Adjust the path to your image file.
    try:
        image = Image.open(r"C:\Users\matia\Desktop\report\step3\picture\default-placeholder.png")
        st.image(image, caption="Bike Sharing Data", use_container_width=True)
    except Exception as e:
        st.error(f"Error loading image: {e}")
