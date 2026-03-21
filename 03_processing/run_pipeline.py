"""
03_processing/run_pipeline.py  —  Medallion ETL launcher
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run from the project root:

    python 03_processing/run_pipeline.py            # full pipeline (bronze → gold)
    python 03_processing/run_pipeline.py --silver   # bronze → silver only
    python 03_processing/run_pipeline.py --gold     # silver → gold only
    python 03_processing/run_pipeline.py --status   # show layer status and exit

Typically called automatically by GitHub Actions after the scraper finishes.
Also useful during local development after manually dropping CSVs into bronze/.
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from config import (
    BRONZE_PATH,
    CITIES,
    DIMENSIONS_PATH,
    FACTS_PATH,
    NOTEBOOK_EXPORTS_PATH,
    SILVER_PATH,
)


# ── Layer status ───────────────────────────────────────────────────────────────

def _layer_status() -> None:
    print("\n  Data layer status")
    print("  " + "─" * 52)

    for city in CITIES:
        files = list((BRONZE_PATH / city).rglob("*.csv")) if (BRONZE_PATH / city).exists() else []
        print(f"  Bronze  {city:<12}  {len(files)} CSV file(s)")

    for city in CITIES:
        files = list((SILVER_PATH / city).glob("*.csv")) if (SILVER_PATH / city).exists() else []
        years = ", ".join(f.stem for f in sorted(files)) or "—"
        print(f"  Silver  {city:<12}  {len(files)} year CSV(s): {years}")

    fact_files = sorted(FACTS_PATH.glob("fact_trips_*.csv")) if FACTS_PATH.exists() else []
    dim_files  = sorted(DIMENSIONS_PATH.glob("*.csv")) if DIMENSIONS_PATH.exists() else []
    nb_exports = list(NOTEBOOK_EXPORTS_PATH.iterdir()) if NOTEBOOK_EXPORTS_PATH.exists() else []

    print(f"  Gold    facts        {len(fact_files)} file(s):  {', '.join(f.stem for f in fact_files) or '—'}")
    print(f"  Gold    dimensions   {len(dim_files)} file(s):  {', '.join(f.stem for f in dim_files) or '—'}")
    print(f"  Gold    exports      {len(nb_exports)} notebook export(s)")
    print()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Urban Cycling Medallion ETL")
    parser.add_argument("--silver", action="store_true", help="Bronze → Silver only")
    parser.add_argument("--gold",   action="store_true", help="Silver → Gold only")
    parser.add_argument("--status", action="store_true", help="Show layer status and exit")
    args = parser.parse_args()

    print("\n" + "═" * 60)
    print("  Urban Cycling — Medallion Pipeline Runner")
    print("═" * 60)

    _layer_status()

    if args.status:
        sys.exit(0)

    from transform import run_etl

    if args.silver and not args.gold:
        run_etl(silver=True, gold=False)
    elif args.gold and not args.silver:
        run_etl(silver=False, gold=True)
    else:
        run_etl(silver=True, gold=True)

    print("\n  ─── Final status ───")
    _layer_status()
