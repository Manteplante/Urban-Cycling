# 03_processing/config.py
#
# Databricks Medallion Architecture
# ──────────────────────────────────────────────────────────────────────────────
#  Bronze  (02_data/bronze/)  Raw scraped CSVs — never modified, always kept
#  Silver  (02_data/silver/)  Cleaned & consolidated by city + year
#  Gold    (02_data/gold/)    Star schema (dims + facts) and ML-ready tables
#                             Also contains: gold/notebook_exports/ for charts
#                             and DataFrames produced in Jupyter notebooks
# ──────────────────────────────────────────────────────────────────────────────
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]

# Medallion layers
BRONZE_PATH = PROJECT_ROOT / "02_data" / "bronze"
SILVER_PATH = PROJECT_ROOT / "02_data" / "silver"
GOLD_PATH   = PROJECT_ROOT / "02_data" / "gold"

# Gold sub-directories
FACTS_PATH            = GOLD_PATH / "facts"
DIMENSIONS_PATH       = GOLD_PATH / "dimensions"
NOTEBOOK_EXPORTS_PATH = GOLD_PATH / "notebook_exports"

# City constants
CITIES          = ["oslo", "bergen", "trondheim"]
CITY_ID_MAP     = {"oslo": 1, "bergen": 2, "trondheim": 3}
ID_CITY_MAP     = {1: "oslo", 2: "bergen", 3: "trondheim"}
CITY_DISPLAY_MAP = {"oslo": "Oslo", "bergen": "Bergen", "trondheim": "Trondheim"}
