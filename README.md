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
uv sync
```

uv creates a local `.venv` in the repository root. To work inside it explicitly,
you can activate it on Windows with:

```bash
.\.venv\Scripts\activate
```

If you prefer not to activate anything, use `uv run ...` for commands.

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
python 01_scraper/scraper_main.py --monthly
```

Or fetch all available months for one specific year:

```bash
python 01_scraper/scraper_main.py --year 2025
```

### 4. Build Silver and Gold

```bash
uv run python 03_processing/run_pipeline.py
```

Optional GCS publish mode:

```bash
$env:GOLD_GCS_UPLOAD="true"
$env:GOLD_GCS_BUCKET="your-private-bucket"
$env:GCS_PROJECT="your-gcp-project"
$env:GCS_SERVICE_ACCOUNT_FILE="cloud-key.json"
uv run python 03_processing/run_pipeline.py
```

This keeps local files in `02_data/gold/` and additionally uploads the same artefacts to:

```text
gs://<bucket>/dimensions/*
gs://<bucket>/facts/*
gs://<bucket>/notebook_exports/*
```

### 5. Start the app

```bash
uv run streamlit run 04_app/home.py
```

### 6. Legacy requirements file

`requirements.txt` is retained as a compatibility bridge for now, but `pyproject.toml`
and `uv.lock` are the source of truth for dependencies.

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

---

## Streamlit Community Cloud deployment foundation

This repository now targets Streamlit Community Cloud behavior:

- You deploy by selecting repository + branch + main file path
- App runs in Streamlit-managed environment (not on your local PC)
- CI is GitHub-hosted and focused on code/app contract validation

### CI workflow

Workflow file: `.github/workflows/ci-community.yml`

It runs on push/PR and performs:

1. Dependency install
2. Python compile check across scraper/processing/app
3. Gold-only app guardrail (`03_processing/ci/check_app_gold_only.py`)
4. Smoke imports for Streamlit service modules

### Deploy in Streamlit Community Cloud

1. Open Streamlit Community Cloud.
2. Choose this repository and branch `main`.
3. Set main file path to `04_app/home.py`.
4. Add app secrets (in Streamlit settings) when needed.

### Data behavior for cloud deployments

Community Cloud containers do not have your local disk. This app supports two modes:

1. Local/repo mode: read from `02_data/gold/*` when files exist.
2. Remote gold mode: set `GOLD_PUBLIC_BASE_URL` and `AVAILABLE_YEARS` so the app reads gold CSVs from a hosted URL.
3. Private GCS mode: set `GOLD_GCS_BUCKET` and Streamlit GCS secrets so the app reads from Google Cloud Storage first and falls back to local files.

Private GCS mode uses the same object layout as local gold:

```text
gs://<bucket>/dimensions/dim_city.csv
gs://<bucket>/dimensions/dim_stations.csv
gs://<bucket>/dimensions/dim_date.csv
gs://<bucket>/facts/fact_trips_2024.csv
gs://<bucket>/facts/fact_trips_2025.csv
gs://<bucket>/facts/fact_top_trip_patterns.csv
gs://<bucket>/notebook_exports/<export>.csv
gs://<bucket>/notebook_exports/<figure>.png
```

Expected remote URL layout:

```
<base>/dimensions/dim_city.csv
<base>/dimensions/dim_stations.csv
<base>/dimensions/dim_date.csv
<base>/facts/fact_trips_2024.csv
<base>/facts/fact_trips_2025.csv
<base>/facts/fact_top_trip_patterns.csv
```

Set these in Streamlit secrets (or environment):

- `GOLD_PUBLIC_BASE_URL`
- `AVAILABLE_YEARS` (example: `2024,2025`)

For private GCS-backed Streamlit reads, add these environment variables:

- `GOLD_GCS_BUCKET`
- `GOLD_GCS_PREFIX` (optional, leave empty for bucket root)
- `AVAILABLE_YEARS` if you want a fallback year list when remote listing is unavailable

And add this to `.streamlit/secrets.toml`:

```toml
[connections.gcs]
type = "service_account"
project_id = "xxx"
private_key_id = "xxx"
private_key = "xxx"
client_email = "xxx"
client_id = "xxx"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "xxx"
```

For ETL-side uploads outside Streamlit, set these environment variables before running the pipeline:

- `GOLD_GCS_UPLOAD=true`
- `GOLD_GCS_BUCKET=<bucket-name>`
- `GOLD_GCS_PREFIX=<optional-prefix>`
- `GCS_PROJECT=<gcp-project-id>`
- `GCS_SERVICE_ACCOUNT_FILE=<path-to-service-account-json>`

### Optional pre-deploy endpoint validation in GitHub Actions

If you fill in `.github/community-cloud-config.json` with:

- `gold_public_base_url`
- `available_years`

then CI workflow `.github/workflows/ci-community.yml` will verify that the
required remote gold CSV endpoints are reachable before deployment updates.

