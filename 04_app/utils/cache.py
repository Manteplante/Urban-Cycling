# Lightweight caching utilities.

import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

from services.gcs_storage import gcs_any_match, gcs_enabled

PROJECT_ROOT = Path(__file__).parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def resolve_env_path(var_name: str, default_relative: str) -> Path:
    raw = (os.getenv(var_name) or default_relative).strip()
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


# Bust all Streamlit data caches (useful for development).
def clear_all_caches() -> None:
    st.cache_data.clear()


# Return True if the gold star schema CSVs have been generated.
def data_exists() -> bool:
    if gcs_enabled() and gcs_any_match("facts", suffixes=(".csv",)):
        return True

    facts_path = resolve_env_path("FACTS_PATH", "02_data/gold/facts")
    return facts_path.exists() and any(facts_path.glob("fact_trips_*.csv"))


# Return True if any notebook exports are available.
def notebook_exports_exist() -> bool:
    if gcs_enabled() and gcs_any_match("notebook_exports", suffixes=(".csv", ".png")):
        return True

    exports = resolve_env_path("NOTEBOOK_EXPORTS_PATH", "02_data/gold/notebook_exports")
    return exports.exists() and any(
        p for p in exports.iterdir() if p.suffix in {".csv", ".png"}
    )

