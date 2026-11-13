"""The mitomap-link-data CLI (CI data release build + init-container materialize)."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from mitomap_link import data_cli

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "mitomap.dump.excerpt.sql"


def test_build_writes_release_assets(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    dump = tmp_path / "mitomap.dump.sql.gz"
    dump.write_bytes(gzip.compress(FIXTURE.read_bytes(), mtime=0))
    out = tmp_path / "release"
    code = data_cli.main(
        [
            "build",
            "--dump",
            str(dump),
            "--last-modified",
            "Wed, 11 Nov 2026 08:01:01 GMT",
            "--output",
            str(out),
            "--revision",
            "a" * 40,
            "--authorization",
            str(ROOT / "release" / "data-authorization.json"),
        ]
    )
    assert code == 0
    manifest = json.loads(capsys.readouterr().out)
    assert manifest["source"]["sha256"] == hashlib.sha256(dump.read_bytes()).hexdigest()
    assert manifest["source"]["last_modified"] == "Wed, 11 Nov 2026 08:01:01 GMT"
    assert (out / "mitomap.sqlite.gz").is_file()


def test_materialize_failure_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(data_cli.settings.data, "reference_root", tmp_path)
    monkeypatch.setattr(data_cli.settings.data, "bundle_url", "https://evil.test/x")
    assert data_cli.main(["materialize"]) == 1
