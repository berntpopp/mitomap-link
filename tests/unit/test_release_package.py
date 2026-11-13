"""Release packaging: content-addressed tag, deterministic gzip, checksums, manifest."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from mitomap_link.ingest.build import SourceInfo, build_database
from mitomap_link.ingest.release import package_release

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "mitomap.dump.excerpt.sql"
AUTH = ROOT / "release" / "data-authorization.json"
SOURCE = SourceInfo("https://mitomap.org/downloads/mitomap.dump.sql.gz", "a" * 64, 9, "x")


def _package(tmp_path: Path, name: str) -> tuple[Path, dict[str, object]]:
    db = tmp_path / f"{name}.sqlite"
    with FIXTURE.open(encoding="utf-8") as fh:
        counts = build_database(fh, db, SOURCE)
    out = tmp_path / name
    return out, package_release(db, out, SOURCE, counts, revision="f" * 40, authorization=AUTH)


def test_assets_checksums_and_tag(tmp_path: Path) -> None:
    out, manifest = _package(tmp_path, "one")
    assert sorted(p.name for p in out.iterdir()) == [
        "SHA256SUMS",
        "data-authorization.json",
        "manifest.json",
        "mitomap.sqlite.gz",
    ]
    bundle = (out / "mitomap.sqlite.gz").read_bytes()
    expanded = gzip.decompress(bundle)
    assert manifest["compressed_sha256"] == hashlib.sha256(bundle).hexdigest()
    assert manifest["expanded_sha256"] == hashlib.sha256(expanded).hexdigest()
    assert manifest["release_tag"] == f"data-mitomap-{manifest['expanded_sha256'][:16]}"
    assert json.loads((out / "manifest.json").read_text()) == manifest
    sums = (out / "SHA256SUMS").read_text().splitlines()
    assert len(sums) == 3 and all(line.endswith(tuple(manifest["assets"])) for line in sums)
    assert manifest["license"]["spdx"] == "CC-BY-3.0"
    assert manifest["transformation"]["revision"] == "f" * 40


def test_packaging_is_deterministic(tmp_path: Path) -> None:
    one, _ = _package(tmp_path, "one")
    two, _ = _package(tmp_path, "two")
    for name in ("mitomap.sqlite.gz", "manifest.json", "SHA256SUMS"):
        assert (one / name).read_bytes() == (two / name).read_bytes()
