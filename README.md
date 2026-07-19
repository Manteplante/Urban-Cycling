# Urban Cycling — Oslo · Bergen · Trondheim

Urban Cycling is a bike-share analytics repository built around a strict Medallion pipeline:

- Bronze: raw monthly CSV files from city portals
- Silver: cleaned and standardised city-year tables
- Gold: star-schema dimensions and fact tables for analytics and app usage

The repository has one clear flow: scrape -> pipeline -> notebook processing workspace -> Streamlit pages.

## Project intent

This is a private, individual project used to test and iterate on two things together:

- a Streamlit app for presenting city bike-share insights
- a data analytics pipeline for scraping, transforming, and modeling data

You can still use this project yourself with your own infrastructure choices.
Google Cloud Storage is included mainly to support production-style Streamlit deployment and larger hosted datasets, but local development works without cloud storage.

Contributions are welcome, especially around analytical choices, metric definitions, transformations, and visualization logic.

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
├── .github/
│   └── workflows/
│       └── ci-community.yml
├── .env.example
├── .python-version
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
├── 04_app/
│   ├── home.py
│   ├── pages/
│   ├── services/
│   ├── components/
│   └── utils/
├── pyproject.toml
├── README.md
├── Taskfile.yml
└── uv.lock
```

---

## Local developer onboarding (uv + task)

This repository uses:

- `uv` for Python dependency and environment management
- `Taskfile.yml` as the cross-platform command runner (Windows + Linux + macOS)

`uv` is used here as a standalone tool. The setup below follows the same standalone-install approach described in the Real Python uv guide [https://realpython.com/python-uv/] while keeping Windows onboarding standardized around **Chocolatey** [https://chocolatey.org/install]

### 1. Install required CLIs

Windows (project-standard): install with Chocolatey.

```bash
# Install uv
choco install uv -y

# Install task (Go Task)
choco install go-task -y
```

If you prefer the standalone installer directly, `uv` also supports:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Linux / macOS:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install task (Go Task)
brew install go-task/tap/go-task
# or see: https://taskfile.dev/installation/
```

If a newly installed command is not recognized, restart your terminal so PATH updates are loaded.

Optional verification:

```bash
uv --version
task --version
```

### 2. Open the repo root and bootstrap

```bash
cd Urban-Cycling
task setup
```

`task setup` runs `uv sync --frozen`, creates a local `.venv` in the repository root, and installs the project notebook kernel (`urban-cycling`) used by workspace notebooks.

### 3. Create local env file

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

### 4. Discover available commands

```bash
task
```

This prints:

- all available tasks
- a command cheat sheet showing the underlying command for each task

### 5. Most common workflows

```bash
# Start app
task app

# Scrape latest monthly files
task scrape:monthly

# Scrape specific year
task scrape:year YEAR=2025

# Run full Bronze -> Silver -> Gold pipeline
task pipeline

# Run notebooks only (rebuild notebook_exports without rerunning ETL)
task notebooks:run

# Show data layer status only
task pipeline:status

# Run CI-style local checks
task ci
```

### 6. Optional GCS publish mode (ETL upload)

Before running pipeline tasks, set these variables:

```bash
# Windows PowerShell
$env:GOLD_GCS_UPLOAD="true"
$env:GOLD_GCS_BUCKET="your-private-bucket"
$env:GCS_PROJECT="your-gcp-project"
$env:GCS_SERVICE_ACCOUNT_FILE="cloud-key.json"

task pipeline
```

This keeps local files in `02_data/gold/` and additionally uploads the same artefacts to:

```text
gs://<bucket>/dimensions/*
gs://<bucket>/facts/*
gs://<bucket>/notebook_exports/*
```

### 7. Direct uv commands (without task)

All task commands can still be run directly. Examples:

```bash
uv run streamlit run 04_app/home.py
uv run python 03_processing/run_pipeline.py --status
uv run python 01_scraper/scraper_main.py --year 2025
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
2. Run full pipeline to build Silver and Gold.
3. During full pipeline runs, workspace notebooks execute automatically and refresh `02_data/gold/notebook_exports/`.
4. Notebook export helpers write artefacts locally and publish to GCS when `GOLD_GCS_UPLOAD=true`.
5. Streamlit page files in `04_app/pages/` read those exports and render maps/visuals.

Notebook auto-execution is enabled for full pipeline runs and intentionally not triggered for `--silver`, `--gold`, and `--top-patterns` modes.

---

## Streamlit Community Cloud deployment foundation

This repository now targets Streamlit Community Cloud behavior:

- You deploy by selecting repository + branch + main file path
- App runs in Streamlit-managed environment (not on your local PC)
- CI is GitHub-hosted and focused on code/app contract validation

### CI workflow

Workflow file: `.github/workflows/ci-community.yml`

It runs on pull requests targeting `dev` and `main`, and performs:

1. Dependency install
2. Python compile check across scraper/processing/app
3. Gold-only app guardrail (`03_processing/ci/check_app_gold_only.py`)
4. Smoke imports for Streamlit service modules
5. Streamlit app page smoke tests

### Branching model (minimal solo workflow)

- `main` = production branch
- `dev` = integration branch
- `feature/*` = short-lived work branches

Expected flow:

1. Create `feature/*` from `dev`.
2. Open PR: `feature/*` -> `dev`.
3. CI passes and PR is merged into `dev`.
4. Open PR: `dev` -> `main`.
5. CI passes and PR is merged into `main`.

### Deploy in Streamlit Community Cloud

1. Open Streamlit Community Cloud.
2. Choose this repository and branch `main`.
3. Set main file path to `04_app/home.py`.
4. Add app secrets (in Streamlit settings) for private GCS access.

Required runtime settings for remote-only app loading:

- `GOLD_GCS_BUCKET`
- Optional: `GOLD_GCS_PREFIX`
- Service account keys under one supported secret layout:
     - `[connections.gcs]` (preferred)
     - `[gcp_service_account]`
     - `[gcs]`
     - or top-level service-account keys

Expected object layout in bucket:

- `dimensions/dim_city.csv`
- `dimensions/dim_stations.csv`
- `dimensions/dim_date.csv`
- `facts/fact_trips_<year>.csv`
- `facts/fact_top_trip_patterns.csv`
- `notebook_exports/*.csv|*.png`

### Why Google Cloud is used in this project

This project uses Google Cloud because the bike-share datasets are large enough to grow into millions of rows across cities and years. That makes them a poor fit for storing directly in GitHub in the same way you might keep a much smaller survey dataset in a repo.

In practice, the repository keeps the code, pipeline, and local development structure, while larger analytical outputs can be stored outside GitHub and read back into the app when needed.

For this reason, the Streamlit app reads cloud-hosted gold data in deployment,
while ETL can still generate local artefacts before optional GCS publishing.

Follow this resource to set up your own: https://docs.streamlit.io/develop/tutorials/databases/gcs

---

## License

This project is licensed under the MIT License.