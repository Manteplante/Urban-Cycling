# Load artefacts exported by Jupyter notebooks.
#
# Notebooks call notebook_bridge.export_df() / export_figure() which save
# files to 02_data/gold/notebook_exports/. This module reads those files
# for display in the Streamlit app.

import pandas as pd
import streamlit as st
from pathlib import Path

from services.gcs_storage import gcs_any_match, gcs_enabled, gcs_list, gcs_read_csv


# Return True if the notebook_exports directory has any artefacts.
def exports_exist() -> bool:
    return gcs_enabled() and gcs_any_match("notebook_exports", suffixes=(".csv", ".png"))


@st.cache_data(ttl=60)   # short TTL so new exports appear quickly
# Return artefact metadata sorted by modification time (newest first).
def list_exports() -> list[dict]:
    if not gcs_enabled():
        return []

    artefacts = []
    for entry in gcs_list("notebook_exports"):
        name = Path(str(entry.get("name") or "")).name
        suffix = Path(name).suffix.lower()
        if suffix == ".csv":
            kind = "dataframe"
        elif suffix == ".png":
            kind = "figure"
        else:
            continue

        artefacts.append({
            "name": Path(name).stem,
            "filename": name,
            "kind": kind,
            "path": str(entry.get("name") or ""),
            "modified": str(entry.get("updated") or ""),
        })

    return sorted(artefacts, key=lambda x: x["filename"], reverse=True)


@st.cache_data(ttl=60)
# Load a CSV export by filename.
def load_export_df(filename: str) -> pd.DataFrame:
    if not gcs_enabled():
        return pd.DataFrame()

    return gcs_read_csv(f"notebook_exports/{filename}")
