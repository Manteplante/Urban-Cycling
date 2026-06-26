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


def resolve_env_path(var_name: str, default_relative: str) -> Path:
	raw = (os.getenv(var_name) or default_relative).strip()
	candidate = Path(raw).expanduser()
	if not candidate.is_absolute():
		candidate = PROJECT_ROOT / candidate
	return candidate.resolve()

# Medallion layers
BRONZE_PATH = resolve_env_path("BRONZE_PATH", "02_data/bronze")
SILVER_PATH = resolve_env_path("SILVER_PATH", "02_data/silver")
GOLD_PATH = resolve_env_path("GOLD_PATH", "02_data/gold")

# Gold sub-directories
FACTS_PATH = resolve_env_path("FACTS_PATH", str(Path("02_data") / "gold" / "facts"))
DIMENSIONS_PATH = resolve_env_path("DIMENSIONS_PATH", str(Path("02_data") / "gold" / "dimensions"))
NOTEBOOK_EXPORTS_PATH = resolve_env_path(
	"NOTEBOOK_EXPORTS_PATH",
	str(Path("02_data") / "gold" / "notebook_exports"),
)

# Optional GCS publishing for gold artefacts
GOLD_GCS_UPLOAD = (os.getenv("GOLD_GCS_UPLOAD") or "false").strip().lower() in {"1", "true", "yes", "on"}
GOLD_GCS_BUCKET = (os.getenv("GOLD_GCS_BUCKET") or "").strip()
GOLD_GCS_PREFIX = (os.getenv("GOLD_GCS_PREFIX") or "").strip().strip("/")
GCS_PROJECT = (os.getenv("GCS_PROJECT") or "").strip()
GCS_SERVICE_ACCOUNT_FILE = (os.getenv("GCS_SERVICE_ACCOUNT_FILE") or "").strip()

# City constants
CITIES          = ["oslo", "bergen", "trondheim"]
CITY_ID_MAP     = {"oslo": 1, "bergen": 2, "trondheim": 3}
ID_CITY_MAP     = {1: "oslo", 2: "bergen", 3: "trondheim"}
CITY_DISPLAY_MAP = {"oslo": "Oslo", "bergen": "Bergen", "trondheim": "Trondheim"}


def gcs_object_path(*parts: str) -> str:
	cleaned = [part.strip("/") for part in parts if part and part.strip("/")]
	if GOLD_GCS_PREFIX:
		return "/".join([GOLD_GCS_PREFIX, *cleaned])
	return "/".join(cleaned)
