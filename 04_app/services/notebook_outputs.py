"""
notebook_outputs.py — Load artefacts exported by Jupyter notebooks.

Notebooks call notebook_bridge.export_df() / export_figure() which save
files to:  02_data/gold/notebook_exports/

This module reads those files back for display in the Streamlit app
(see pages/04_insights.py).
"""

import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime

PROJECT_ROOT      = Path(__file__).parents[2]
EXPORTS_PATH      = PROJECT_ROOT / "02_data" / "gold" / "notebook_exports"


def exports_exist() -> bool:
    """Return True if the notebook_exports directory has any artefacts."""
    if not EXPORTS_PATH.exists():
        return False
    return any(EXPORTS_PATH.iterdir())


@st.cache_data(ttl=60)   # short TTL so new exports appear quickly
def list_exports() -> list[dict]:
    """Return a list of artefact metadata dicts, sorted by modification time (newest first).

    Each dict contains:
        name        str   filename without extension
        filename    str   full filename  (e.g. oslo_trips_2024.csv)
        kind        str   'dataframe' | 'figure'
        path        Path
        modified    str   human-readable timestamp
    """
    if not EXPORTS_PATH.exists():
        return []

    artefacts = []
    for p in EXPORTS_PATH.iterdir():
        if p.suffix == ".csv":
            kind = "dataframe"
        elif p.suffix == ".png":
            kind = "figure"
        else:
            continue

        artefacts.append({
            "name":     p.stem,
            "filename": p.name,
            "kind":     kind,
            "path":     p,
            "modified": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        })

    return sorted(artefacts, key=lambda x: x["path"].stat().st_mtime, reverse=True)


@st.cache_data(ttl=60)
def load_export_df(filename: str) -> pd.DataFrame:
    """Load a CSV export by filename."""
    path = EXPORTS_PATH / filename
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as exc:
        st.error(f"Could not read {filename}: {exc}")
        return pd.DataFrame()
