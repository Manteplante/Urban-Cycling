from __future__ import annotations

from pathlib import Path
from typing import Optional

from config import GCS_PROJECT, GCS_SERVICE_ACCOUNT_FILE, GOLD_GCS_BUCKET, GOLD_GCS_UPLOAD, gcs_object_path

try:
    import gcsfs
except Exception:
    gcsfs = None


def gcs_available() -> bool:
    return gcsfs is not None


def gcs_bucket_configured() -> bool:
    return bool(GOLD_GCS_BUCKET)


def gcs_publish_enabled() -> bool:
    return GOLD_GCS_UPLOAD and gcs_bucket_configured()


def build_gcs_uri(relative_path: str) -> str:
    object_path = gcs_object_path(relative_path)
    if not GOLD_GCS_BUCKET:
        raise ValueError("GOLD_GCS_BUCKET is not configured.")
    return f"gs://{GOLD_GCS_BUCKET}/{object_path}"


def get_gcs_filesystem() -> "gcsfs.GCSFileSystem":
    if gcsfs is None:
        raise RuntimeError("gcsfs is not installed. Add it to requirements.txt before publishing to GCS.")

    kwargs: dict[str, object] = {}
    if GCS_PROJECT:
        kwargs["project"] = GCS_PROJECT

    token: Optional[str] = GCS_SERVICE_ACCOUNT_FILE or None
    if token:
        return gcsfs.GCSFileSystem(token=token, **kwargs)
    return gcsfs.GCSFileSystem(**kwargs)


def upload_file(local_path: Path, relative_path: str) -> str:
    if not local_path.exists():
        raise FileNotFoundError(f"Cannot upload missing file: {local_path}")

    destination = build_gcs_uri(relative_path)
    fs = get_gcs_filesystem()
    fs.put(str(local_path), destination)
    return destination