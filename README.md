# Urban Cycling — Oslo · Bergen · Trondheim

Urban Cycling is a bike-share analytics repository built around a strict Medallion pipeline:

- Bronze: raw monthly CSV files from city portals
- Silver: cleaned and standardised city-year tables
- Gold: star-schema dimensions and fact tables for analytics and app usage

The repository has one clear flow: scrape -> pipeline -> notebook processing workspace -> Streamlit pages.

---

## Architecture overview

```
01_scraper/          Fetches raw monthly CSVs from city portals
     ↓
02_data/bronze/      Raw source data (never manually edited)
     ↓
03_processing/       Pipeline stage 1: Bronze -> Silver
     ↓
02_data/silver/      Clean city-year tables
     ↓
03_processing/       Pipeline stage 2: Silver -> Gold
     ↓
02_data/gold/        Star schema + notebook exports consumed by app pages
     ↓
04_app/              Streamlit application pages
```

---

## Repository structure

```
.
├── 01_scraper/
│   ├── scraper_main.py
│   └── csv_fetcher.py, csv_cleaner.py, enabler.py
├── 02_data/
│   ├── bronze/{city}/
│   ├── silver/{city}/
│   └── gold/
│       ├── dimensions/
│       ├── facts/
│       └── notebook_exports/
├── 03_processing/
│   ├── config.py
│   ├── transform.py
│   ├── run_pipeline.py
│   ├── notebook_bridge.py
│   └── workspace/
│       ├── 02_temporal_patterns.ipynb
│       ├── 03_work_trips.ipynb
│       ├── 04_seasonal_trends.ipynb
│       ├── 05_top_routes_stations.ipynb
│       ├── 06_yearly_trends.ipynb
│       ├── 07_least_used_stations.ipynb
│       └── utils.py
└── 04_app/
    ├── home.py
    ├── pages/
    ├── services/
    ├── components/
    └── utils/
```

---

## Run the project (pipeline specific)

### 1. Create environment and install dependencies

```bash
python -m venv bysykkel
bysykkel\Scripts\activate
pip install -r requirements.txt
```

### 2. Create local env file

```bash
Copy-Item .env.example .env
```

### 3. Load Bronze data

Place source CSV files in:

```
02_data/bronze/oslo/
02_data/bronze/bergen/
02_data/bronze/trondheim/
```

Or fetch latest source files:

```bash
python 01_scraper/scraper_main.py
```

### 4. Build Silver and Gold

```bash
python 03_processing/run_pipeline.py
```

### 5. Start the app

```bash
cd 04_app
streamlit run home.py
```

---

## ETL pipeline contract

Pipeline code lives in `03_processing/transform.py` and is executed via `03_processing/run_pipeline.py`.

- Stage 1 (Bronze -> Silver): standardises source schemas and writes one CSV per city/year.
- Stage 2 (Silver -> Gold): builds analytics-ready dimensions and yearly fact tables.

Gold outputs used by app and notebooks:

- `02_data/gold/dimensions/dim_city.csv`
- `02_data/gold/dimensions/dim_stations.csv`
- `02_data/gold/dimensions/dim_date.csv`
- `02_data/gold/facts/fact_trips_{year}.csv`
- `02_data/gold/notebook_exports/*.csv|*.json|*.png` (exports created in notebooks)

---

## Notebook workspace role

`03_processing/workspace/` notebooks are working analysis workspaces.

This is where data is processed for chapter-level insights and where visuals are developed before app rendering.
In practice, notebooks are used to:

- shape and aggregate dataframes for each analytics topic
- validate metric logic on top of silver/gold data
- create plots and tables for temporal, route, seasonal, yearly, and least-used analyses
- export approved dataframes and figures to `02_data/gold/notebook_exports/`

So the notebooks are not just exploratory notes. They are the processing workspace that defines how visuals are created.

---

## Streamlit pages data source

`04_app/pages/` files render maps and visuals from repository data contracts:

- Gold tables loaded through `04_app/services/gold.py`
- Notebook dataframe exports loaded through `04_app/services/notebook_outputs.py`

This means page files are consumers, not places for heavy data processing.
Data shaping is done upstream in pipeline + notebook workspace, then pages focus on UI rendering.

Examples:

- maps page uses station/volume-ready data to render map views
- temporal/seasonal/routes pages use notebook-exported dataframes and figures for charts
- yearly and least-used views follow the same pattern: export in notebook, render in page

---

## End-to-end flow used in this repo

1. Scrape or drop raw monthly CSVs into Bronze.
2. Run pipeline to build Silver and Gold.
3. Open notebooks in `03_processing/workspace/` and process topic dataframes.
4. Export dataframe/figure artifacts to `02_data/gold/notebook_exports/`.
5. Streamlit page files in `04_app/pages/` read those exports and render maps/visuals.

