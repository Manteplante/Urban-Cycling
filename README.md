# Urban Cycling — Oslo · Bergen · Trondheim

Bike-share analytics platform built on a **Medallion architecture** (Bronze → Silver → Gold).  
Data is scraped automatically every month, processed through a multi-stage ETL pipeline, analysed in Jupyter notebooks, and presented in a Streamlit application.

---

## Table of Contents

1. [Architecture overview](#architecture-overview)
2. [Project structure](#project-structure)
3. [Quick start](#quick-start)
4. [ETL pipeline](#etl-pipeline)
5. [Analysis workspace](#analysis-workspace)
6. [Streamlit app](#streamlit-app)
7. [Adding new analyses](#adding-new-analyses)
8. [GitHub Actions](#github-actions)

---

## Architecture overview

```
01_scraper/          Scrapes monthly CSV files from city open-data portals
     ↓
02_data/bronze/      Raw CSVs — never modified, the single source of truth
     ↓  (Stage 1)
02_data/silver/      Cleaned & partitioned by city and year
     ↓  (Stage 2)
02_data/gold/        Star schema (dims + facts) consumed by the app and notebooks
                     Also: gold/notebook_exports/ for charts and tables
                           produced in the analysis workspace
     ↓
03_processing/       ETL pipeline  +  analysis workspace (notebooks)
04_app/              Streamlit application
```

The data layers mirror a Databricks Medallion architecture — each layer is
independent, fully reproducible from the layer above it, and versioned in Git
(CSV files are gitignored; folder structure and `.gitkeep` placeholders are not).

---

## Project structure

```
.
├── 01_scraper/              Monthly scraper (do not modify)
│   ├── scraper_main.py
│   └── ...
├── 02_data/
│   ├── bronze/{city}/       Raw scraped CSVs → oslo/, bergen/, trondheim/
│   ├── silver/{city}/       Cleaned per-year CSVs → oslo/2024.csv, ...
│   └── gold/
│       ├── dimensions/      dim_city.csv, dim_stations.csv, dim_date.csv
│       ├── facts/           fact_trips_2023.csv, fact_trips_2024.csv, ...
│       └── notebook_exports/  Charts and tables saved from notebooks
├── 03_processing/
│   ├── config.py            Central path constants (Bronze/Silver/Gold paths)
│   ├── transform.py         ETL pipeline (3 stages)
│   ├── run_pipeline.py      CLI launcher for the ETL pipeline
│   ├── notebook_bridge.py   Data bridge: load from any layer, export to app
│   └── workspace/           ← Analysis workspace (notebooks live here)
│       ├── utils.py         Shared analysis toolkit
│       ├── 01_explore.ipynb Exploratory data analysis
│       ├── 02_temporal_patterns.ipynb Temporal patterns export notebook
│       ├── 03_models.ipynb  Regression + clustering models
│       ├── 04_seasonal_trends.ipynb Seasonal trend export notebook
│       └── 05_top_routes_stations.ipynb Top routes export notebook
└── 04_app/
    ├── home.py              Streamlit entrypoint (landing page)
    ├── pages/
    │   ├── 02_maps.py       Interactive station map
     │   ├── 03_temporal_patterns.py  Temporal chapter page
     │   ├── 04_top_routes_stations.py Top routes chapter page
     │   └── 05_seasonal_variations.py Seasonal chapter page
    ├── services/
    │   ├── gold.py          Gold catalog — the data access layer
    │   └── ...
    └── components/          Reusable charts, filters, metrics
```

---

## Quick start

### 1 — Install dependencies

```bash
python -m venv bysykkel
# Windows
bysykkel\Scripts\activate
# macOS / Linux
source bysykkel/bin/activate

pip install -r requirements.txt
```

### 2 — Add CSV data to bronze

Drop raw CSV files from any of the three city portals into the matching bronze folder:

```
02_data/bronze/oslo/          ← Oslo data
02_data/bronze/bergen/        ← Bergen data
02_data/bronze/trondheim/     ← Trondheim data
```

Or run the scraper manually to fetch the latest month:

```bash
cd 01_scraper
python scraper_main.py
```

### 3 — Run the ETL pipeline

```bash
# Full pipeline: bronze → silver → gold
python 03_processing/run_pipeline.py

# Just bronze → silver (normalise and partition by year)
python 03_processing/run_pipeline.py --silver

# Just silver → gold (build star schema)
python 03_processing/run_pipeline.py --gold

# Show what data is in each layer without running anything
python 03_processing/run_pipeline.py --status
```

Example `--status` output:

```
  Data layer status
  ────────────────────────────────────────────────────
  Bronze  oslo          6 CSV file(s)
  Bronze  bergen        6 CSV file(s)
  Bronze  trondheim     6 CSV file(s)
  Silver  oslo          2 year CSV(s): 2023, 2024
  Silver  bergen        2 year CSV(s): 2023, 2024
  Silver  trondheim     2 year CSV(s): 2023, 2024
  Gold    facts         2 file(s): fact_trips_2023, fact_trips_2024
  Gold    dimensions    3 file(s): dim_city, dim_date, dim_stations
  Gold    exports       4 notebook export(s)
```

### 4 — Launch the Streamlit app

```bash
cd 04_app
streamlit run home.py
```

---

## ETL pipeline

The pipeline in `03_processing/transform.py` runs in two stages.

### Stage 1 — Bronze → Silver

Reads all raw CSVs from `02_data/bronze/{city}/`, normalises column names
across city providers (e.g. `starttime` → `started_at`), adds `city_id`,
and writes one clean CSV per city × year:

```
02_data/silver/oslo/2023.csv
02_data/silver/oslo/2024.csv
02_data/silver/bergen/2024.csv
...
```

### Stage 2 — Silver → Gold

Builds a star schema from all silver data:

| File | Columns |
|------|---------|
| `gold/dimensions/dim_city.csv` | `city_id, city_name, display_name, country` |
| `gold/dimensions/dim_stations.csv` | `station_id, station_name, latitude, longitude, city_id` |
| `gold/dimensions/dim_date.csv` | `date_id, date, year, month, month_name, day, day_of_week, is_weekend, quarter` |
| `gold/facts/fact_trips_{year}.csv` | `trip_id, city_id, start_station_id, end_station_id, date_id, start_hour, duration_seconds` |

To run just one stage:

```bash
python 03_processing/run_pipeline.py --silver   # stage 1 only
python 03_processing/run_pipeline.py --gold     # stage 2 only
```

---

## Analysis workspace

The `03_processing/workspace/` folder is a self-contained analysis environment.
It mirrors the Databricks notebook workspace pattern — open any `.ipynb`, run cells,
and export results directly to the Streamlit app.

### Importing the toolkit

Every notebook starts with:

```python
import sys; sys.path.insert(0, "..")
from utils import (
     load, load_app_ready, describe, feature_matrix,
     plot_hourly, plot_monthly, plot_top_stations, plot_duration_dist, plot_city_comparison,
     export_df, export_figure,
     CITIES, CITY_DISPLAY_MAP,
)
```

### Loading data

```python
# All cities, all years — silver layer (best for EDA)
df = load()

# Single city, single year
df = load("oslo", 2024)

# All years for one city
df = load("bergen")

# Gold fact table for a specific year (pre-built star schema)
df = load(year=2024, layer="gold")

# Raw bronze data (pre-cleaning)
from utils import load_bronze
raw = load_bronze("trondheim")
```

### Describing your data

```python
describe(df)
# Returns an extended DataFrame with nulls, null %, and dtype for each column
```

### Built-in plots

```python
fig = plot_hourly(df, title="Oslo 2024 — Trips by Hour")
fig = plot_monthly(df)
fig = plot_top_stations(df, n=15)
fig = plot_duration_dist(df, max_minutes=45)
fig = plot_city_comparison(df)   # requires load() with all cities
```

All plot functions return a `matplotlib.Figure` — display inline, save with
`fig.savefig(...)`, or export to the app with `export_figure(...)`.

### Exporting to the Streamlit app

Anything you export appears automatically in the **Insights** page of the app
after you refresh the browser.

```python
# Export a DataFrame as a table
top_stations = df.groupby("start_station_name").size().nlargest(10).reset_index()
export_df("oslo_top_stations_2024", top_stations)

# Export a matplotlib figure
fig = plot_hourly(df)
export_figure("oslo_hourly_2024", fig)
```

Files are saved to `02_data/gold/notebook_exports/` and picked up by the app.

### Building an ML feature matrix

```python
X, y = feature_matrix(df, target="duration_seconds")
# X contains: hour, day_of_week, month, is_weekend, city_id
# y contains: duration in seconds

from sklearn.linear_model import LinearRegression
model = LinearRegression().fit(X, y)
```

The full regression + clustering workflow is in `workspace/03_models.ipynb`.

---

## Streamlit app

### Pages

| Page | Path | What it shows |
|------|------|---------------|
| Home | `home.py` | KPIs, city cards, navigation |
| Maps | `pages/02_maps.py` | Folium station map, bubble size = trip volume |
| Temporal Patterns | `pages/03_temporal_patterns.py` | Hourly, daily, and monthly demand patterns |
| Top Routes & Stations | `pages/04_top_routes_stations.py` | Busiest route corridors and stations |
| Seasonal Variations | `pages/05_seasonal_variations.py` | Winter vs summer comparisons |

### Gold catalog — the data access layer

All pages load data through a single import:

```python
from services.gold import gold
```

The `gold` object behaves like a semantic model — no paths, no SQL, no joins.

```python
# All trips for Oslo in 2024
df = gold.for_city("oslo", year=2024)

# Fluent query builder — chain filters
df = gold.query().city("oslo").year(2024).load()
df = gold.query().cities(["oslo", "bergen"]).years([2023, 2024]).load()
df = gold.query().city("oslo").year(2024).month(6).load()   # June only

# Dimension tables
stations = gold.stations()   # all stations with lat/lon
dates    = gold.dates()      # full date dimension
cities   = gold.cities()     # city reference table

# Discovery
gold.available_years()       # [2023, 2024]
gold.available_cities()      # ['oslo', 'bergen', 'trondheim']
gold.schema()                # column names for each table
gold.status()                # data health check
```

The returned DataFrame is always a **fully denormalised, joined** table —
station names, city names, and date attributes are already resolved.

### Sidebar filters

Every page uses `sidebar_filters()` to render filter widgets and return
a pre-seeded `GoldQuery`:

```python
from components.filters import sidebar_filters

query = sidebar_filters(key_prefix="my_page")
df = query.load()
```

The sidebar automatically populates itself with the cities and years that
have actual data — no hardcoded lists.

### Adding a new page

1. Create `04_app/pages/05_mypage.py` (the number prefix controls menu order).
2. Load data with the gold catalog:

```python
from components.filters import sidebar_filters
from services.gold import gold

query = sidebar_filters(key_prefix="mypage")
df = query.load()
```

3. Build charts with [Plotly](https://plotly.com/python/) or the helpers in
   `components/charts.py`, then render with `st.plotly_chart(fig, use_container_width=True)`.

---

## Adding new analyses

### Option A — Notebook → App (no code change in the app)

1. Open any notebook in `03_processing/workspace/` (or create a new one).
2. Run your analysis.
3. Export results:

```python
export_figure("my_insight_chart", fig)
export_df("my_insight_table", df)
```

4. Open the matching Streamlit chapter page — your exported data is loaded automatically.

### Option B — New standalone chapter page

1. Create a new notebook in `03_processing/workspace/`.
2. Export a table with `export_df("my_chapter_data", df)`.
3. Add a new page in `04_app/pages/` that reads the export via `services/notebook_outputs.py`.
4. Link the page from `04_app/home.py`.

### Option C — New standalone page

Follow the steps in [Adding a new page](#adding-a-new-page) above.

---

## GitHub Actions

The workflow in `.github/workflows/bysykkel_scraper.yml` runs on demand
(`workflow_dispatch`) and:

1. Runs `01_scraper/scraper_main.py` — downloads the latest monthly CSVs
   into `02_data/bronze/{city}/`.
2. Runs `python 03_processing/run_pipeline.py` — builds silver and gold layers.
3. Prints a layer status report.

Trigger it manually from the **Actions** tab on GitHub, or extend the `on:`
block to run on a schedule:

```yaml
on:
  schedule:
    - cron: "0 6 1 * *"   # 06:00 UTC on the 1st of every month
  workflow_dispatch:
```

