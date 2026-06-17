from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REQUIRED_STATIC_PATHS = (
    "dimensions/dim_city.csv",
    "dimensions/dim_stations.csv",
    "dimensions/dim_date.csv",
    "facts/fact_top_trip_patterns.csv",
)


def normalize_base_url(raw: str) -> str:
    return raw.strip().rstrip("/")


def parse_years(raw: str) -> list[int]:
    years: list[int] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            years.append(int(token))
        except ValueError as exc:
            raise ValueError(f"Invalid year token: {token}") from exc
    return sorted(set(years))


def iter_required_urls(base_url: str, years: Iterable[int]) -> list[str]:
    urls = [f"{base_url}/{path}" for path in REQUIRED_STATIC_PATHS]
    urls.extend(f"{base_url}/facts/fact_trips_{year}.csv" for year in years)
    return urls


def check_url(url: str, timeout: int) -> tuple[bool, str]:
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            status_code = getattr(response, "status", response.getcode())
            body = response.read(256)
    except HTTPError as exc:
        return False, f"unexpected status code {exc.code}"
    except URLError as exc:
        return False, f"request failed: {exc.reason}"
    except Exception as exc:
        return False, f"request failed: {exc}"

    if status_code != 200:
        return False, f"unexpected status code {status_code}"

    if not body.strip():
        return False, "empty response body"

    return True, "ok"


def load_config(config_path: Path) -> tuple[str, list[int]]:
    if not config_path.exists():
        return "", []

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    base_url = str(payload.get("gold_public_base_url") or "").strip()
    years_raw = payload.get("available_years") or []
    years = [int(year) for year in years_raw if str(year).strip()]
    return base_url, sorted(set(years))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate remotely hosted gold CSV endpoints for Streamlit Community Cloud deployments."
    )
    parser.add_argument("--base-url", help="Public base URL hosting gold/facts and gold/dimensions CSV files")
    parser.add_argument("--years", help="Comma-separated year list, for example 2024,2025")
    parser.add_argument(
        "--config",
        default=str(Path(".github") / "community-cloud-config.json"),
        help="Optional JSON config with gold_public_base_url and available_years",
    )
    parser.add_argument("--timeout", type=int, default=20, help="Per-request timeout in seconds")
    args = parser.parse_args()

    config_base_url, config_years = load_config(Path(args.config))
    base_url = normalize_base_url(args.base_url or config_base_url)
    years = config_years

    if args.years:
        try:
            years = parse_years(args.years)
        except ValueError as exc:
            print(f"ERROR: {exc}")
            return 1

    if not base_url and not years:
        print("SKIP: No remote gold config provided.")
        return 0

    if not years:
        print("ERROR: At least one year must be provided via --years")
        return 1

    if not base_url.startswith(("https://", "http://")):
        print("ERROR: --base-url must start with http:// or https://")
        return 1

    failures: list[tuple[str, str]] = []
    for url in iter_required_urls(base_url, years):
        ok, detail = check_url(url, args.timeout)
        if ok:
            print(f"OK: {url}")
        else:
            print(f"ERROR: {url} | {detail}")
            failures.append((url, detail))

    if failures:
        print(f"ERROR: Remote gold validation failed for {len(failures)} endpoint(s)")
        return 1

    print("OK: All required remote gold endpoints are reachable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())