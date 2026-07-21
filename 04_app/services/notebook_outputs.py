# Load artefacts exported by Jupyter notebooks.
#
# Notebooks call notebook_bridge.export_df() / export_figure() which save
# files to 02_data/gold/notebook_exports/. This module reads those files
# for display in the Streamlit app.

import os
import pandas as pd
import streamlit as st
from pathlib import Path

from services.gcs_storage import gcs_any_match, gcs_enabled, gcs_list, gcs_read_csv


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _debug_memory_enabled() -> bool:
    env_raw = (os.getenv("APP_DEBUG_MEMORY") or "").strip()
    return bool(env_raw) and _is_truthy(env_raw)


def _dataframe_memory_mb(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    return float(df.memory_usage(deep=True).sum()) / (1024 * 1024)


def _emit_memory_debug(message: str) -> None:
    if not message or not _debug_memory_enabled():
        return
    print(f"[app-memory] {message}")


def _optimize_export_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    optimized = df.copy()

    int_columns = optimized.select_dtypes(include=["int", "int64", "Int64"]).columns
    for column in int_columns:
        optimized[column] = pd.to_numeric(optimized[column], downcast="integer")

    float_columns = optimized.select_dtypes(include=["float32"]).columns
    for column in float_columns:
        optimized[column] = optimized[column].astype("float64")

    return optimized


# Return True if the notebook_exports directory has any artefacts.
def exports_exist() -> bool:
    return gcs_enabled() and gcs_any_match("notebook_exports", suffixes=(".csv", ".png"))


@st.cache_data(ttl=60, max_entries=1)   # short TTL so new exports appear quickly
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


@st.cache_data(ttl=60, max_entries=8)
def _load_export_df_cached(filename: str, required_columns: tuple[str, ...]) -> pd.DataFrame:
    if not gcs_enabled():
        return pd.DataFrame()

    read_kwargs: dict[str, object] = {}
    if required_columns:
        read_kwargs["usecols"] = list(required_columns)

    result = _optimize_export_frame(gcs_read_csv(f"notebook_exports/{filename}", **read_kwargs))
    _emit_memory_debug(
        f"export cache-miss file={filename} rows={len(result):,} cols={len(result.columns)} mem_mb={_dataframe_memory_mb(result):.2f} requested={list(required_columns) or 'all'}"
    )
    return result


# Load a CSV export by filename.
def load_export_df(
    filename: str,
    required_columns: list[str] | tuple[str, ...] | None = None,
) -> pd.DataFrame:
    return _load_export_df_cached(filename, tuple(required_columns or ()))
