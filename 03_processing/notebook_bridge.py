"""
notebook_bridge.py — Jupyter ↔ Streamlit data bridge
═══════════════════════════════════════════════════════════════════════════════

Import this in any notebook under 03_processing/tests/ to:

  • Load data from silver (per-city/year) or gold (star schema) without
    needing Streamlit in scope.

  • Export a DataFrame or a Matplotlib figure to gold/notebook_exports/.
    The Streamlit page 04_insights.py will automatically pick these up and
    display them in the app.

Example usage in a notebook cell:
─────────────────────────────────
    import sys; sys.path.insert(0, "..")   # so we can find notebook_bridge
    from notebook_bridge import load_silver, load_gold, export_df, export_figure

    df = load_silver("oslo", 2024)
    top5 = df.groupby("start_station_name").size().nlargest(5)

    fig, ax = plt.subplots()
    top5.plot.barh(ax=ax)
    ax.set_title("Top 5 Oslo departure stations 2024")

    export_df("oslo_top_departures_2024", top5.reset_index())
    export_figure("oslo_top_departures_2024", fig)
─────────────────────────────────
The exports will appear in the Streamlit app under the "Notebook Insights"
page (04_insights.py) after the next browser refresh.
"""

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

def load_bronze(city: str) -> pd.DataFrame:
    """Load all raw bronze CSVs for a city into a single DataFrame.

    Parameters
    ----------
    city : str
        One of 'oslo', 'bergen', 'trondheim' (case-insensitive).
    """
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


def load_silver(city: str, year: int = None) -> pd.DataFrame:
    """Load cleaned silver data for a city.

    Parameters
    ----------
    city : str
        One of 'oslo', 'bergen', 'trondheim'.
    year : int, optional
        If given, loads only that year.  If None, loads all available years.
    """
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


def load_gold(table_name: str, parse_dates: list = None) -> pd.DataFrame:
    """Load a gold table by name (without the .csv extension).

    Available tables (after running the ETL):
        dim_city, dim_stations, dim_date,
        fact_trips_2022, fact_trips_2023, fact_trips_2024, …

    Parameters
    ----------
    table_name : str
        e.g. ``'dim_stations'`` or ``'fact_trips_2024'``.
    parse_dates : list, optional
        Column names to parse as dates.
    """
    for search_path in [DIMENSIONS_PATH, FACTS_PATH]:
        path = search_path / f"{table_name}.csv"
        if path.exists():
            return pd.read_csv(path, parse_dates=parse_dates or [], low_memory=False)

    raise FileNotFoundError(
        f"Gold table '{table_name}' not found in {DIMENSIONS_PATH} or {FACTS_PATH}.\n"
        "Run `python 03_processing/transform.py` first."
    )


def list_silver_years(city: str) -> list:
    """Return sorted list of available silver years for a city."""
    city_silver = SILVER_PATH / city.lower()
    if not city_silver.exists():
        return []
    return sorted(int(f.stem) for f in city_silver.glob("*.csv"))


# ── Exporters ─────────────────────────────────────────────────────────────────

def export_df(name: str, df: pd.DataFrame) -> Path:
    """Save *df* to gold/notebook_exports/{name}.csv.

    The file will appear in the Streamlit Notebook Insights page.

    Parameters
    ----------
    name : str
        A descriptive filename without extension, e.g.
        ``'oslo_top_departures_2024'``.
    df : pd.DataFrame
        The DataFrame to export.

    Returns
    -------
    Path
        Absolute path to the written file.
    """
    out = NOTEBOOK_EXPORTS_PATH / f"{name}.csv"
    df.to_csv(out, index=False)
    print(f"[bridge] Exported DataFrame → {out}")
    return out


def export_figure(name: str, fig, dpi: int = 150) -> Path:
    """Save a Matplotlib figure to gold/notebook_exports/{name}.png.

    The image will appear in the Streamlit Notebook Insights page.

    Parameters
    ----------
    name : str
        A descriptive filename without extension.
    fig : matplotlib.figure.Figure
        The figure to save.
    dpi : int, optional
        Resolution (default 150).

    Returns
    -------
    Path
        Absolute path to the written file.
    """
    out = NOTEBOOK_EXPORTS_PATH / f"{name}.png"
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    print(f"[bridge] Exported figure  → {out}")
    return out


def list_exports() -> list:
    """Return a list of all exported artefacts (relative filenames)."""
    return sorted(
        p.name
        for p in NOTEBOOK_EXPORTS_PATH.iterdir()
        if p.suffix in {".csv", ".png"}
    )
