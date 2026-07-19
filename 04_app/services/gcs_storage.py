from __future__ import annotations

import os
import json
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

_GCS_AUTH_ERROR = ""


def _set_gcs_auth_error(message: str) -> None:
    global _GCS_AUTH_ERROR
    _GCS_AUTH_ERROR = message.strip()
    _emit_local_auth_debug(_GCS_AUTH_ERROR)


def _short_error(exc: Exception) -> str:
    text = str(exc).strip()
    return text[:240] if text else exc.__class__.__name__


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _debug_gcs_errors_enabled() -> bool:
    env_raw = (os.getenv("APP_DEBUG_GCS_ERRORS") or "").strip()
    if env_raw:
        return _is_truthy(env_raw)

    secrets = _streamlit_secrets_dict()
    connections = _to_dict(secrets.get("connections", {}))
    for raw in (
        str(secrets.get("APP_DEBUG_GCS_ERRORS") or ""),
        str(secrets.get("app_debug_gcs_errors") or ""),
        str(connections.get("APP_DEBUG_GCS_ERRORS") or ""),
    ):
        if raw.strip():
            return _is_truthy(raw)

    return False


def _emit_local_auth_debug(message: str) -> None:
    if not message or not _debug_gcs_errors_enabled():
        return
    print(f"[gcs-auth] {message}")


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    try:
        return dict(value)
    except Exception:
        return {}


def _streamlit_secrets_dict() -> dict[str, Any]:
    if st is None:
        return {}

    try:
        return _to_dict(st.secrets)
    except Exception:
        return {}


def _secret_text(*keys: str) -> str:
    secrets = _streamlit_secrets_dict()
    for key in keys:
        raw = secrets.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return ""


def _json_object(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    return _to_dict(parsed)


def _load_service_account_file(path_value: str) -> dict[str, Any]:
    candidate = Path(path_value).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate

    try:
        text = candidate.read_text(encoding="utf-8")
    except Exception:
        return {}

    parsed = _json_object(text)
    if not parsed:
        return {}

    private_key = parsed.get("private_key")
    if isinstance(private_key, str):
        parsed["private_key"] = private_key.replace("\\n", "\n")

    if parsed and "type" not in parsed:
        parsed["type"] = "service_account"

    return parsed


def _gcs_bucket() -> str:
    env_bucket = (os.getenv("GOLD_GCS_BUCKET") or "").strip()
    if env_bucket:
        return env_bucket

    secrets = _streamlit_secrets_dict()
    gcs_section = _to_dict(secrets.get("gcs", {}))
    connections = _to_dict(secrets.get("connections", {}))
    conn_gcs_section = _to_dict(_to_dict(secrets.get("connections", {})).get("gcs", {}))

    for candidate in (
        _secret_text("GOLD_GCS_BUCKET", "gold_gcs_bucket", "bucket", "gcs_bucket"),
        str(connections.get("GOLD_GCS_BUCKET") or "").strip(),
        str(gcs_section.get("bucket") or "").strip(),
        str(conn_gcs_section.get("bucket") or "").strip(),
    ):
        if candidate:
            return candidate

    return ""


def _gcs_prefix() -> str:
    env_prefix = (os.getenv("GOLD_GCS_PREFIX") or "").strip().strip("/")
    if env_prefix:
        return env_prefix

    secrets = _streamlit_secrets_dict()
    gcs_section = _to_dict(secrets.get("gcs", {}))
    connections = _to_dict(secrets.get("connections", {}))
    conn_gcs_section = _to_dict(_to_dict(secrets.get("connections", {})).get("gcs", {}))

    for candidate in (
        _secret_text("GOLD_GCS_PREFIX", "gold_gcs_prefix", "prefix", "gcs_prefix"),
        str(connections.get("GOLD_GCS_PREFIX") or "").strip(),
        str(gcs_section.get("prefix") or "").strip(),
        str(conn_gcs_section.get("prefix") or "").strip(),
    ):
        normalized = candidate.strip().strip("/")
        if normalized:
            return normalized

    return ""


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
    return bool(_gcs_bucket())


def gcs_object_path(relative_path: str) -> str:
    relative = relative_path.strip().strip("/")
    prefix = _gcs_prefix()
    if prefix:
        return f"{prefix}/{relative}"
    return relative


def gcs_uri(relative_path: str) -> str:
    return f"gs://{_gcs_bucket()}/{gcs_object_path(relative_path)}"


def _gcs_credentials() -> dict[str, Any]:
    if st is None:
        return {}

    try:
        secrets = _streamlit_secrets_dict()

        # Preferred layout for this repository.
        connections = _to_dict(secrets.get("connections", {}))
        conn_gcs = _to_dict(connections.get("gcs", {}))
        if conn_gcs:
            creds = conn_gcs
        else:
            # Common Streamlit layout.
            gcp_service_account = _to_dict(secrets.get("gcp_service_account", {}))
            if not gcp_service_account:
                # Some setups store the full JSON as a single secret string.
                gcp_service_account = _json_object(
                    _secret_text("gcp_service_account", "GCP_SERVICE_ACCOUNT_JSON", "GOOGLE_APPLICATION_CREDENTIALS_JSON")
                )
            if gcp_service_account:
                creds = gcp_service_account
            else:
                # Alternative section name.
                gcs_section = _to_dict(secrets.get("gcs", {}))
                if gcs_section and any(k in gcs_section for k in ("project_id", "client_email", "private_key")):
                    creds = gcs_section
                else:
                    # Top-level service-account keys.
                    top_level_keys = {
                        "type",
                        "project_id",
                        "private_key_id",
                        "private_key",
                        "client_email",
                        "client_id",
                        "auth_uri",
                        "token_uri",
                        "auth_provider_x509_cert_url",
                        "client_x509_cert_url",
                    }
                    creds = {k: secrets[k] for k in top_level_keys if k in secrets}

                    if not creds:
                        env_json = (
                            os.getenv("GCP_SERVICE_ACCOUNT_JSON")
                            or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
                            or ""
                        ).strip()
                        if env_json:
                            creds = _json_object(env_json)

                    if not creds:
                        # Local/dev and some hosted environments may provide
                        # a service-account file path instead of inline JSON.
                        file_hint = (
                            _secret_text("GCS_SERVICE_ACCOUNT_FILE", "gcs_service_account_file", "GOOGLE_APPLICATION_CREDENTIALS")
                            or os.getenv("GCS_SERVICE_ACCOUNT_FILE")
                            or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                            or ""
                        ).strip()
                        if file_hint:
                            creds = _load_service_account_file(file_hint)

        normalized = _to_dict(creds)
        private_key = normalized.get("private_key")
        if isinstance(private_key, str):
            normalized["private_key"] = private_key.replace("\\n", "\n")

        if normalized and "type" not in normalized:
            normalized["type"] = "service_account"

        return normalized
    except Exception:
        return {}


@cache_resource()
def get_gcs_filesystem() -> Optional[Any]:
    if gcsfs is None or not gcs_enabled():
        _set_gcs_auth_error("GCS disabled or gcsfs package not available")
        return None

    creds = _gcs_credentials()
    if not creds:
        try:
            # Last-resort option when platform credentials are wired via ADC.
            fs = gcsfs.GCSFileSystem(token="google_default")
            _set_gcs_auth_error("")
            return fs
        except Exception as exc:
            _set_gcs_auth_error(f"No usable secrets credentials and ADC fallback failed: {_short_error(exc)}")
            return None

    project = creds.get("project_id") or None
    kwargs: dict[str, Any] = {}
    if project:
        kwargs["project"] = project

    try:
        fs = gcsfs.GCSFileSystem(token=creds, **kwargs)
        _set_gcs_auth_error("")
        return fs
    except Exception as exc:
        _set_gcs_auth_error(f"Service-account credential initialization failed: {_short_error(exc)}")
        return None


def gcs_runtime_status() -> dict[str, Any]:
    fs = get_gcs_filesystem()
    debug_enabled = _debug_gcs_errors_enabled()
    return {
        "enabled": gcs_enabled(),
        "bucket": _gcs_bucket(),
        "prefix": _gcs_prefix(),
        "has_credentials": bool(_gcs_credentials()),
        "filesystem_ready": fs is not None,
        "auth_error": _GCS_AUTH_ERROR if debug_enabled else "",
    }


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