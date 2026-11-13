"""Durable compare-and-swap snapshots for anonymous RevisionGate workspaces."""
from __future__ import annotations

import hashlib
import json
from threading import Lock

from google.api_core.exceptions import GoogleAPIError, NotFound, PreconditionFailed
from google.auth.exceptions import GoogleAuthError
from google.cloud import storage
from google.cloud.storage.exceptions import DataCorruption
from google.cloud.storage.retry import DEFAULT_RETRY
from requests.exceptions import RequestException


class StoreConflict(Exception):
    """Another request has already advanced the stored generation."""


class StoreUnavailable(Exception):
    """The caller cannot safely read or commit the authoritative review."""


_RETRY = DEFAULT_RETRY.with_timeout(8)
_STORAGE_ERRORS = (GoogleAPIError, GoogleAuthError, RequestException, DataCorruption)


class GCSStore:
    """One private object per workspace, using credentials attached to the runtime."""

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self._client = None
        self._lock = Lock()

    def _blob(self, key: str):
        # Object listings and cloud audit logs must not contain the browser's bearer key.
        name = hashlib.sha256(key.encode("utf-8")).hexdigest()
        with self._lock:
            if self._client is None:
                self._client = storage.Client()
            return self._client.bucket(self.bucket_name).blob(f"workspaces/{name}.json")

    def read(self, key: str) -> tuple[int, dict | None]:
        try:
            blob = self._blob(key)
            # The generation header comes from the same download as these bytes.
            data = json.loads(blob.download_as_bytes(timeout=8, retry=_RETRY))
            if not isinstance(data, dict) or not blob.generation:
                raise StoreUnavailable()
            return int(blob.generation), data
        except NotFound:
            return 0, None
        except (ValueError, *_STORAGE_ERRORS):
            raise StoreUnavailable() from None

    def write(self, key: str, expected_generation: int, run: dict) -> int:
        try:
            blob = self._blob(key)
            blob.cache_control = "private, no-store"
            blob.upload_from_string(
                json.dumps(run, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8"),
                content_type="application/json",
                if_generation_match=expected_generation,
                timeout=8,
                retry=_RETRY,
            )
            if not blob.generation:
                raise StoreUnavailable()
            return int(blob.generation)
        except PreconditionFailed:
            raise StoreConflict() from None
        except _STORAGE_ERRORS:
            raise StoreUnavailable() from None
