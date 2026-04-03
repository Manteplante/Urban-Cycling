# 03_processing/workspace/utils.py
# Minimal notebook helpers used by current workspace notebooks.

import importlib
import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).parent
_PROC = _HERE.parent
sys.path.insert(0, str(_PROC))
sys.path.insert(0, str(_PROC.parent / "04_app"))

import notebook_bridge as _bridge

try:
    from services.gold import gold as _app_gold
except Exception:
    _app_gold = None

__all__ = ["load_app_ready", "export_df"]


def load_app_ready(
    city: str | None = None,
    years: list[int] | None = None,
    months: list[int] | None = None,
) -> pd.DataFrame:
    if _app_gold is None:
        raise ImportError(
            "Could not import Streamlit gold catalog. "
            "Ensure 04_app/services/gold.py exists and dependencies are installed."
        )

    query = _app_gold.query()
    if city:
        query = query.city(city)
    if years:
        query = query.years(years)
    if months:
        query = query.months(months)
    return query.load()


def export_df(name: str, df: pd.DataFrame):
    # Refresh bridge module to avoid stale notebook kernel imports.
    importlib.reload(_bridge)
    return _bridge.export_df(name, df)
