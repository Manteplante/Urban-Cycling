# Load artefacts exported by Jupyter notebooks.
#
# Notebooks call notebook_bridge.export_df() / export_figure() which save
# files to 02_data/gold/notebook_exports/. This module reads those files
# for display in the Streamlit app.

import os
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from services.gcs_storage import gcs_any_match, gcs_enabled, gcs_list, gcs_read_csv

PROJECT_ROOT      = Path(__file__).parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def resolve_env_path(var_name: str, default_relative: str) -> Path:
    raw = (os.getenv(var_name) or default_relative).strip()
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


EXPORTS_PATH = resolve_env_path("NOTEBOOK_EXPORTS_PATH", "02_data/gold/notebook_exports")


# Return True if the notebook_exports directory has any artefacts.
def exports_exist() -> bool:
    if gcs_enabled() and gcs_any_match("notebook_exports", suffixes=(".csv", ".png")):
        return True
    if not EXPORTS_PATH.exists():
        return False
    return any(EXPORTS_PATH.iterdir())


@st.cache_data(ttl=60)   # short TTL so new exports appear quickly
# Return artefact metadata sorted by modification time (newest first).
def list_exports() -> list[dict]:
    if gcs_enabled():
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

        if artefacts:
            return sorted(artefacts, key=lambda x: x["filename"], reverse=True)

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
# Load a CSV export by filename.
def load_export_df(filename: str) -> pd.DataFrame:
    path = EXPORTS_PATH / filename
    if gcs_enabled():
        remote_df = gcs_read_csv(f"notebook_exports/{filename}")
        if not remote_df.empty:
            return remote_df

    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as exc:
        st.error(f"Could not read {filename}: {exc}")
        return pd.DataFrame()
