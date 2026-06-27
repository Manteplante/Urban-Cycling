# 03_processing/run_pipeline.py — Medallion ETL launcher
#
# Run from the project root:
#     python 03_processing/run_pipeline.py            # full pipeline (bronze -> gold)
#     python 03_processing/run_pipeline.py --years 2025
#                                                   # run bronze -> gold only for selected year(s)
#     python 03_processing/run_pipeline.py --silver   # bronze -> silver only
#     python 03_processing/run_pipeline.py --gold     # silver -> gold only
#     python 03_processing/run_pipeline.py --top-patterns [--years 2024 2025]
#                                                   # rebuild only top route patterns
#     python 03_processing/run_pipeline.py --status   # show layer status and exit

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
from transform import run_etl, run_gold_top_patterns_only
from run_notebooks import run_workspace_notebooks


# ── Layer status ───────────────────────────────────────────────────────────────

def layer_status() -> None:
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
    top_pattern_path = FACTS_PATH / "fact_top_trip_patterns.csv"
    has_top_patterns = top_pattern_path.exists()
    dim_files  = sorted(DIMENSIONS_PATH.glob("*.csv")) if DIMENSIONS_PATH.exists() else []
    nb_exports = list(NOTEBOOK_EXPORTS_PATH.iterdir()) if NOTEBOOK_EXPORTS_PATH.exists() else []

    print(f"  Gold    facts        {len(fact_files)} file(s):  {', '.join(f.stem for f in fact_files) or '—'}")
    print(f"  Gold    top_patterns {'present' if has_top_patterns else 'missing':<8}  {top_pattern_path.name}")
    print(f"  Gold    dimensions   {len(dim_files)} file(s):  {', '.join(f.stem for f in dim_files) or '—'}")
    print(f"  Gold    exports      {len(nb_exports)} notebook export(s)")
    print()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Urban Cycling Medallion ETL")
    parser.add_argument("--silver", action="store_true", help="Bronze → Silver only")
    parser.add_argument("--gold",   action="store_true", help="Silver → Gold only")
    parser.add_argument("--top-patterns", action="store_true", help="Rebuild only fact_top_trip_patterns.csv")
    parser.add_argument("--years", nargs="+", type=int, help="Optional year filter for ETL and --top-patterns")
    parser.add_argument("--status", action="store_true", help="Show layer status and exit")
    args = parser.parse_args()

    print("\n" + "═" * 60)
    print("  Urban Cycling — Medallion Pipeline Runner")
    print("═" * 60)

    layer_status()

    if args.status:
        sys.exit(0)

    should_run_notebooks = False

    if args.top_patterns:
        run_gold_top_patterns_only(years=args.years)
    elif args.silver and not args.gold:
        run_etl(silver=True, gold=False, years=args.years)
    elif args.gold and not args.silver:
        run_etl(silver=False, gold=True, years=args.years)
    else:
        run_etl(silver=True, gold=True, years=args.years)
        should_run_notebooks = True

    if should_run_notebooks:
        print("\n  ─── Notebook workspace refresh ───")
        run_workspace_notebooks(kernel_name="urban-cycling", timeout=1200)

    print("\n  ─── Final status ───")
    layer_status()
