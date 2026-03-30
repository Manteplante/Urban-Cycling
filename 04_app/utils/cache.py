# Lightweight caching utilities.

import streamlit as st
from pathlib import Path


# Bust all Streamlit data caches (useful for development).
def clear_all_caches() -> None:
    st.cache_data.clear()


# Return True if the gold star schema CSVs have been generated.
def data_exists() -> bool:
    facts_path = Path(__file__).parents[2] / "02_data" / "gold" / "facts"
    return facts_path.exists() and any(facts_path.glob("fact_trips_*.csv"))


# Return True if any notebook exports are available.
def notebook_exports_exist() -> bool:
    exports = Path(__file__).parents[2] / "02_data" / "gold" / "notebook_exports"
    return exports.exists() and any(
        p for p in exports.iterdir() if p.suffix in {".csv", ".png"}
    )

