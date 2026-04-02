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
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parents[1]

# Load repository-level environment variables once for all pipeline modules.
load_dotenv(PROJECT_ROOT / ".env")


def _resolve_env_path(var_name: str, default_relative: str) -> Path:
	raw = (os.getenv(var_name) or default_relative).strip()
	candidate = Path(raw).expanduser()
	if not candidate.is_absolute():
		candidate = PROJECT_ROOT / candidate
	return candidate.resolve()

# Medallion layers
BRONZE_PATH = _resolve_env_path("BRONZE_PATH", "02_data/bronze")
SILVER_PATH = _resolve_env_path("SILVER_PATH", "02_data/silver")
GOLD_PATH = _resolve_env_path("GOLD_PATH", "02_data/gold")

# Gold sub-directories
FACTS_PATH = _resolve_env_path("FACTS_PATH", str(Path("02_data") / "gold" / "facts"))
DIMENSIONS_PATH = _resolve_env_path("DIMENSIONS_PATH", str(Path("02_data") / "gold" / "dimensions"))
NOTEBOOK_EXPORTS_PATH = _resolve_env_path(
	"NOTEBOOK_EXPORTS_PATH",
	str(Path("02_data") / "gold" / "notebook_exports"),
)

# City constants
CITIES          = ["oslo", "bergen", "trondheim"]
CITY_ID_MAP     = {"oslo": 1, "bergen": 2, "trondheim": 3}
ID_CITY_MAP     = {1: "oslo", 2: "bergen", 3: "trondheim"}
CITY_DISPLAY_MAP = {"oslo": "Oslo", "bergen": "Bergen", "trondheim": "Trondheim"}
