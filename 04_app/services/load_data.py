import pandas as pd
import streamlit as st
from pathlib import Path

# Define data paths
PROJECT_ROOT = Path(__file__).parents[2]
GOLD_PATH = PROJECT_ROOT / "02_data" / "03_gold"

# Load any table from the gold layer with caching.

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_gold_table(table_name: str, parse_dates: list = None) -> pd.DataFrame:
    
    file_path = GOLD_PATH / f"{table_name}.csv"
    
    if not file_path.exists():
        st.error(f"File not found: {file_path}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(file_path, parse_dates=parse_dates)
        return df
    except Exception as e:
        st.error(f"Error loading {table_name}: {str(e)}")
        return pd.DataFrame()