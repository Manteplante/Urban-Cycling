"""Execute workspace notebooks in deterministic order for app exports."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import nbformat
from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor

WORKSPACE_DIR = Path(__file__).parent / "workspace"
WORKSPACE_NOTEBOOKS = [
    "02_temporal_patterns.ipynb",
    "03_work_trips.ipynb",
    "04_seasonal_trends.ipynb",
    "05_top_routes_stations.ipynb",
    "06_yearly_trends.ipynb",
    "07_least_used_stations.ipynb",
]


def execute_notebook(path: Path, kernel_name: str, timeout: int) -> None:
    print(f"[notebooks] Running {path.name}...")
    started = time.time()

    with path.open("r", encoding="utf-8") as handle:
        notebook = nbformat.read(handle, as_version=4)

    executor = ExecutePreprocessor(timeout=timeout, kernel_name=kernel_name)
    resources = {"metadata": {"path": str(path.parent)}}
    executor.preprocess(notebook, resources=resources)

    with path.open("w", encoding="utf-8") as handle:
        nbformat.write(notebook, handle)

    elapsed = time.time() - started
    print(f"[notebooks] Completed {path.name} in {elapsed:.1f}s")


def run_workspace_notebooks(kernel_name: str, timeout: int) -> None:
    missing = [name for name in WORKSPACE_NOTEBOOKS if not (WORKSPACE_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing notebook(s): {', '.join(missing)}")

    print("[notebooks] Workspace execution started")
    print(f"[notebooks] Kernel: {kernel_name}")
    print(f"[notebooks] Directory: {WORKSPACE_DIR}")

    for name in WORKSPACE_NOTEBOOKS:
        notebook_path = WORKSPACE_DIR / name
        try:
            execute_notebook(notebook_path, kernel_name=kernel_name, timeout=timeout)
        except CellExecutionError as exc:
            raise RuntimeError(f"Notebook failed: {name}\n{exc}") from exc

    print("[notebooks] All workspace notebooks completed successfully.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all processing workspace notebooks")
    parser.add_argument(
        "--kernel-name",
        default="urban-cycling",
        help="Kernel id to execute notebooks with",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1200,
        help="Per-notebook execution timeout in seconds",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_workspace_notebooks(kernel_name=args.kernel_name, timeout=args.timeout)
