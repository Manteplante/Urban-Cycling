# notebook_bridge.py — Jupyter <-> Streamlit data bridge
#
# Import this in notebooks to load bronze/silver/gold data and export
# DataFrames or figures to 02_data/gold/notebook_exports for app display.

import sys
from pathlib import Path

import pandas as pd

# ── Path resolution works whether you run from project root or 03_processing/ ─
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
from config import (
    BRONZE_PATH,
    DIMENSIONS_PATH,
    FACTS_PATH,
    NOTEBOOK_EXPORTS_PATH,
    SILVER_PATH,
)

NOTEBOOK_EXPORTS_PATH.mkdir(parents=True, exist_ok=True)


# ── Loaders ───────────────────────────────────────────────────────────────────

# Load all raw bronze CSVs for a city into a single DataFrame.
def load_bronze(city: str) -> pd.DataFrame:
    city = city.lower()
    city_path = BRONZE_PATH / city
    if not city_path.exists():
        raise FileNotFoundError(f"Bronze folder not found: {city_path}")

    frames = [
        pd.read_csv(f, low_memory=False)
        for f in sorted(city_path.rglob("*.csv"))
    ]
    if not frames:
        raise FileNotFoundError(f"No CSVs found in {city_path}")
    return pd.concat(frames, ignore_index=True)


# Load cleaned silver data for a city.
# If year is set, load only that year; otherwise load all available years.
def load_silver(city: str, year: int = None) -> pd.DataFrame:
    city = city.lower()
    city_silver = SILVER_PATH / city

    if not city_silver.exists():
        raise FileNotFoundError(
            f"Silver folder not found: {city_silver}\n"
            "Run `python 03_processing/transform.py --silver` first."
        )

    if year is not None:
        path = city_silver / f"{year}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Silver file not found: {path}")
        return pd.read_csv(path, low_memory=False)

    frames = [
        pd.read_csv(f, low_memory=False)
        for f in sorted(city_silver.glob("*.csv"))
    ]
    if not frames:
        raise FileNotFoundError(f"No silver CSV files found for {city}")
    return pd.concat(frames, ignore_index=True)


# Load a gold table by name (without .csv), e.g. dim_stations or fact_trips_2024.
def load_gold(table_name: str, parse_dates: list = None) -> pd.DataFrame:
    for search_path in [DIMENSIONS_PATH, FACTS_PATH]:
        path = search_path / f"{table_name}.csv"
        if path.exists():
            return pd.read_csv(path, parse_dates=parse_dates or [], low_memory=False)

    raise FileNotFoundError(
        f"Gold table '{table_name}' not found in {DIMENSIONS_PATH} or {FACTS_PATH}.\n"
        "Run `python 03_processing/transform.py` first."
    )


# Return sorted list of available silver years for a city.
def list_silver_years(city: str) -> list:
    city_silver = SILVER_PATH / city.lower()
    if not city_silver.exists():
        return []
    return sorted(int(f.stem) for f in city_silver.glob("*.csv"))


# ── Exporters ─────────────────────────────────────────────────────────────────

# Save df to 02_data/gold/notebook_exports/{name}.csv and return the written path.
def export_df(name: str, df: pd.DataFrame) -> Path:
    out = NOTEBOOK_EXPORTS_PATH / f"{name}.csv"
    df.to_csv(out, index=False)
    print(f"[bridge] Exported DataFrame → {out}")
    return out


# Save a Matplotlib figure to 02_data/gold/notebook_exports/{name}.png.
# Returns the written file path.
def export_figure(name: str, fig, dpi: int = 150) -> Path:
    out = NOTEBOOK_EXPORTS_PATH / f"{name}.png"
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    print(f"[bridge] Exported figure  → {out}")
    return out


# Return all exported artefact filenames.
def list_exports() -> list:
    return sorted(
        p.name
        for p in NOTEBOOK_EXPORTS_PATH.iterdir()
        if p.suffix in {".csv", ".png"}
    )
