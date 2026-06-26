from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from dotenv import load_dotenv

try:
    import streamlit as st
    import streamlit.runtime as st_runtime
except Exception:
    st = None
    st_runtime = None

try:
    import gcsfs
except Exception:
    gcsfs = None

PROJECT_ROOT = Path(__file__).parents[2]
load_dotenv(PROJECT_ROOT / ".env")

GOLD_GCS_BUCKET = (os.getenv("GOLD_GCS_BUCKET") or "").strip()
GOLD_GCS_PREFIX = (os.getenv("GOLD_GCS_PREFIX") or "").strip().strip("/")


def cache_resource():
    if st is None:
        def decorator(func):
            return func
        return decorator

    try:
        if st_runtime is None or not st_runtime.exists():
            def decorator(func):
                return func
            return decorator
    except Exception:
        pass

    return st.cache_resource


def gcs_enabled() -> bool:
    return bool(GOLD_GCS_BUCKET)


def gcs_object_path(relative_path: str) -> str:
    relative = relative_path.strip().strip("/")
    if GOLD_GCS_PREFIX:
        return f"{GOLD_GCS_PREFIX}/{relative}"
    return relative


def gcs_uri(relative_path: str) -> str:
    return f"gs://{GOLD_GCS_BUCKET}/{gcs_object_path(relative_path)}"


def _gcs_credentials() -> dict[str, Any]:
    if st is None:
        return {}

    try:
        connections = st.secrets.get("connections", {})
        creds = connections.get("gcs", {})
        return dict(creds)
    except Exception:
        return {}


@cache_resource()
def get_gcs_filesystem() -> Optional["gcsfs.GCSFileSystem"]:
    if gcsfs is None or not gcs_enabled():
        return None

    creds = _gcs_credentials()
    if not creds:
        return None

    project = creds.get("project_id") or None
    kwargs: dict[str, Any] = {}
    if project:
        kwargs["project"] = project

    try:
        return gcsfs.GCSFileSystem(token=creds, **kwargs)
    except Exception:
        return None


def gcs_exists(relative_path: str) -> bool:
    fs = get_gcs_filesystem()
    if fs is None:
        return False

    try:
        return fs.exists(gcs_uri(relative_path))
    except Exception:
        return False


def gcs_read_csv(relative_path: str, **kwargs) -> pd.DataFrame:
    fs = get_gcs_filesystem()
    if fs is None:
        return pd.DataFrame()

    try:
        with fs.open(gcs_uri(relative_path), "rb") as handle:
            return pd.read_csv(handle, **kwargs)
    except Exception:
        return pd.DataFrame()


def gcs_list(relative_prefix: str) -> list[dict[str, Any]]:
    fs = get_gcs_filesystem()
    if fs is None:
        return []

    try:
        listing = fs.ls(gcs_uri(relative_prefix), detail=True)
    except Exception:
        return []

    return listing if isinstance(listing, list) else []


def gcs_any_match(relative_prefix: str, suffixes: tuple[str, ...] | None = None) -> bool:
    entries = gcs_list(relative_prefix)
    if not suffixes:
        return bool(entries)

    suffixes = tuple(s.lower() for s in suffixes)
    for entry in entries:
        name = str(entry.get("name") or "")
        if name.lower().endswith(suffixes):
            return True
    return False