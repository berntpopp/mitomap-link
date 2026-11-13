"""Package a built snapshot as the four immutable data-release assets."""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
from dataclasses import asdict
from pathlib import Path

from mitomap_link.ingest.build import SCHEMA_VERSION, SourceInfo

BUNDLE = "mitomap.sqlite.gz"
ASSETS = (BUNDLE, "data-authorization.json", "manifest.json")
TAG_PREFIX = "data-mitomap-"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def package_release(
    database: Path,
    out: Path,
    source: SourceInfo,
    record_counts: dict[str, int],
    *,
    revision: str,
    authorization: Path,
) -> dict[str, object]:
    """Write bundle, manifest, authorization and SHA256SUMS into ``out``; return the manifest."""
    out.mkdir(parents=True, exist_ok=False)
    bundle = out / BUNDLE
    with database.open("rb") as src, bundle.open("wb") as raw:
        # mtime=0 and no filename keep the gzip header free of wall-clock/host data.
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as gz:
            shutil.copyfileobj(src, gz)
    auth = json.loads(authorization.read_text(encoding="utf-8"))
    shutil.copyfile(authorization, out / "data-authorization.json")
    expanded = _sha256(database)
    manifest: dict[str, object] = {
        "release_tag": f"{TAG_PREFIX}{expanded[:16]}",
        "schema_version": SCHEMA_VERSION,
        "compressed_sha256": _sha256(bundle),
        "expanded_sha256": expanded,
        "source": asdict(source),
        "record_counts": record_counts,
        "transformation": {"tool": "mitomap-link-data build", "revision": revision},
        "license": {
            "spdx": auth["license_spdx"],
            "name": auth["license_name"],
            "terms_url": auth["terms_url"],
        },
        "attribution": auth["attribution"],
        "authorization": {"reviewer": auth["reviewer"], "reviewed_at": auth["reviewed_at"]},
        "research_use_only": True,
        "assets": list(ASSETS),
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    sums = "".join(f"{_sha256(out / name)}  {name}\n" for name in sorted(ASSETS))
    (out / "SHA256SUMS").write_text(sums, encoding="utf-8")
    return manifest
