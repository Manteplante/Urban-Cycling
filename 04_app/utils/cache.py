# Lightweight caching utilities.

import streamlit as st

from services.gcs_storage import gcs_any_match, gcs_enabled


# Bust all Streamlit data caches (useful for development).
def clear_all_caches() -> None:
    st.cache_data.clear()


# Return True if the gold star schema CSVs have been generated.
def data_exists() -> bool:
    return gcs_enabled() and gcs_any_match("facts", suffixes=(".csv",))


# Return True if any notebook exports are available.
def notebook_exports_exist() -> bool:
    return gcs_enabled() and gcs_any_match("notebook_exports", suffixes=(".csv", ".png"))

