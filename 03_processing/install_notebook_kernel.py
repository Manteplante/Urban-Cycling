"""Install or refresh the Jupyter kernel used by workspace notebooks."""

from __future__ import annotations

import argparse
import subprocess
import sys


def install_kernel(name: str, display_name: str) -> None:
    cmd = [
        sys.executable,
        "-m",
        "ipykernel",
        "install",
        "--user",
        "--name",
        name,
        "--display-name",
        display_name,
    ]
    print("[kernel] Installing notebook kernel...")
    print(f"[kernel] Command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"[kernel] Installed/updated kernel '{name}' ({display_name}).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install project notebook kernel")
    parser.add_argument("--name", default="urban-cycling", help="Kernel id")
    parser.add_argument(
        "--display-name",
        default="Urban Cycling (.venv)",
        help="Kernel display name shown in Jupyter/VS Code",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    install_kernel(name=args.name, display_name=args.display_name)
