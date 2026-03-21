# Workspace Runbook (Silver -> Gold -> Streamlit)

Use this folder as the analysis entrypoint, then export final outputs for the app.

## 1) Refresh data layers

From project root:

```bash
python 03_processing/run_pipeline.py
```

## 2) Work in notebooks with one shared loader

At the top of a notebook:

```python
import sys; sys.path.insert(0, "..")
from utils import load, load_app_ready, export_df, export_figure
```

Common patterns:

```python
# Silver (EDA / feature work)
df_silver = load("oslo", 2024)

# App-ready denormalized gold (same shape used in Streamlit)
df_app = load_app_ready(city="Oslo", years=[2024], months=[6, 7, 8])
```

## 3) Keep output contracts app-friendly

When exporting notebook outputs for Streamlit insights:
- Keep table columns snake_case
- Include city and year columns where relevant
- Keep one topic per export file

```python
export_df("oslo_summer_station_summary", df_summary)
export_figure("oslo_summer_hourly_profile", fig)
```

## 4) Streamlit reads from gold only

Do not read silver directly in the app. The app should consume only gold-layer tables
(and notebook exports when needed).

That keeps processing logic in 03_processing and presentation logic in 04_app.
