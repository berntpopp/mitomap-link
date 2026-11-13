"""Init-container step: fetch the pinned data release, verify it, select it atomically.

Runs once before the request-facing app starts (``mitomap-link-data materialize``).
The bundle is accepted only from GitHub release hosts, within size caps, and only when
both the compressed and the expanded SHA-256 match the pin. The verified snapshot lands
in ``<root>/<compressed_sha256>/`` via an atomic rename, so the app can never observe a
partial or unverified file.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import uuid
import zlib
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx

from mitomap_link.config import MitomapDataConfig
from mitomap_link.exceptions import DataUnavailableError
from mitomap_link.store.identity import identity_record, open_verified

ALLOWED_HOSTS = frozenset(
    {"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}
)
_MAX_REDIRECTS = 5
_SQLITE_HEADER = b"SQLite format 3\x00"


def _download(cfg: MitomapDataConfig, dest: Path) -> None:
    url, digest, written = cfg.bundle_url, hashlib.sha256(), 0
    with httpx.Client(follow_redirects=False, timeout=cfg.download_timeout) as client:
        for _ in range(_MAX_REDIRECTS + 1):
            parts = urlsplit(url)
            if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS:
                raise DataUnavailableError("Data bundle URL is not an approved release host.")
            with client.stream("GET", url) as response:
                if response.is_redirect:
                    url = urljoin(url, response.headers["location"])
                    continue
                response.raise_for_status()
                with dest.open("xb") as fh:
                    for chunk in response.iter_bytes(1 << 16):
                        written += len(chunk)
                        if written > cfg.max_compressed_bytes:
                            raise DataUnavailableError("Data bundle exceeds its size cap.")
                        digest.update(chunk)
                        fh.write(chunk)
                break
        else:
            raise DataUnavailableError("Too many redirects fetching the data bundle.")
    if digest.hexdigest() != cfg.compressed_sha256:
        raise DataUnavailableError("Data bundle digest does not match the pin.")


def _expand(cfg: MitomapDataConfig, bundle: Path, database: Path) -> None:
    digest, written = hashlib.sha256(), 0
    with gzip.open(bundle, "rb") as src, database.open("xb") as dst:
        while chunk := src.read(1 << 20):
            written += len(chunk)
            if written > cfg.max_expanded_bytes:
                raise DataUnavailableError("Expanded snapshot exceeds its size cap.")
            digest.update(chunk)
            dst.write(chunk)
        dst.flush()
        os.fsync(dst.fileno())
    if digest.hexdigest() != cfg.expanded_sha256:
        raise DataUnavailableError("Expanded snapshot digest does not match the pin.")
    with database.open("rb") as fh:
        if fh.read(len(_SQLITE_HEADER)) != _SQLITE_HEADER:
            raise DataUnavailableError("Data bundle is not a SQLite database.")


def materialize(cfg: MitomapDataConfig) -> Path:
    """Ensure ``<root>/<compressed_sha256>/`` holds the verified snapshot; return it."""
    target = cfg.reference_root / cfg.compressed_sha256
    try:
        open_verified(cfg)
        return target
    except DataUnavailableError:
        pass
    staging = cfg.reference_root / f".staging-{uuid.uuid4().hex}"
    staging.mkdir(parents=True)
    try:
        bundle = staging / "mitomap.sqlite.gz"
        _download(cfg, bundle)
        database = staging / "mitomap.sqlite"
        _expand(cfg, bundle, database)
        bundle.unlink()
        database.chmod(0o444)
        (staging / "identity.json").write_text(
            json.dumps(identity_record(cfg), sort_keys=True) + "\n", encoding="utf-8"
        )
        if target.exists():
            shutil.rmtree(target)
        os.replace(staging, target)
    except (OSError, httpx.HTTPError, zlib.error, EOFError) as exc:
        raise DataUnavailableError("Data bundle could not be materialized.") from exc
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return target
