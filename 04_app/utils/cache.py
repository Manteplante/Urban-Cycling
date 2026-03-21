"""Lightweight caching utilities."""

import streamlit as st
from pathlib import Path


def clear_all_caches() -> None:
    """Bust all Streamlit data caches (useful for development)."""
    st.cache_data.clear()


def data_exists() -> bool:
    """Return True if the gold star schema CSVs have been generated."""
    facts_path = Path(__file__).parents[2] / "02_data" / "gold" / "facts"
    return facts_path.exists() and any(facts_path.glob("fact_trips_*.csv"))


def notebook_exports_exist() -> bool:
    """Return True if any notebook exports are available."""
    exports = Path(__file__).parents[2] / "02_data" / "gold" / "notebook_exports"
    return exports.exists() and any(
        p for p in exports.iterdir() if p.suffix in {".csv", ".png"}
    )

