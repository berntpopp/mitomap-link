"""Prove the served snapshot is the pinned release before answering any request."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mitomap_link.config import MitomapDataConfig
from mitomap_link.exceptions import DataUnavailableError


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def identity_record(cfg: MitomapDataConfig) -> dict[str, str]:
    """The identity the init step writes and the app re-checks."""
    return {
        "release_tag": cfg.release_tag,
        "compressed_sha256": cfg.compressed_sha256,
        "expanded_sha256": cfg.expanded_sha256,
    }


def expected_identity(cfg: MitomapDataConfig) -> dict[str, str]:
    """The release this build is configured to serve (fleet runtime-v1 ``expected``)."""
    return {"release_tag": cfg.release_tag, "digest": f"sha256:{cfg.compressed_sha256}"}


def open_verified(cfg: MitomapDataConfig) -> tuple[Path, dict[str, str]]:
    """Return the verified SQLite path and the observed (``actual``) release identity."""
    target = cfg.reference_root / cfg.compressed_sha256
    database, identity_path = target / "mitomap.sqlite", target / "identity.json"
    if any(p.is_symlink() or not p.is_file() for p in (database, identity_path)):
        raise DataUnavailableError("The MITOMAP snapshot has not been materialized.")
    try:
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DataUnavailableError("The MITOMAP snapshot identity is unreadable.") from exc
    if identity != identity_record(cfg) or _sha256(database) != cfg.expanded_sha256:
        raise DataUnavailableError("The MITOMAP snapshot does not match its pin.")
    actual = {
        "release_tag": str(identity["release_tag"]),
        "digest": f"sha256:{identity['compressed_sha256']}",
    }
    return database, actual
