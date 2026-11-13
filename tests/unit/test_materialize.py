"""Init-container materialization and the runtime identity the app reports."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import httpx
import pytest
import respx

from mitomap_link.config import MitomapDataConfig
from mitomap_link.exceptions import DataUnavailableError
from mitomap_link.store.identity import open_verified
from mitomap_link.store.materialize import materialize

URL = "https://github.com/berntpopp/mitomap-link/releases/download/data-mitomap-0123456789abcdef/mitomap.sqlite.gz"
ASSET = "https://release-assets.githubusercontent.com/x/mitomap.sqlite.gz"


def _config(
    fixture_database: Path, root: Path, **overrides: object
) -> tuple[MitomapDataConfig, bytes]:
    expanded = fixture_database.read_bytes()
    bundle = gzip.compress(expanded, mtime=0)
    values: dict[str, object] = {
        "release_tag": "data-mitomap-0123456789abcdef",
        "compressed_sha256": hashlib.sha256(bundle).hexdigest(),
        "expanded_sha256": hashlib.sha256(expanded).hexdigest(),
        "bundle_url": URL,
        "reference_root": root,
        **overrides,
    }
    return MitomapDataConfig.model_validate(values), bundle


@respx.mock
def test_materialize_verifies_and_is_idempotent(fixture_database: Path, tmp_path: Path) -> None:
    cfg, bundle = _config(fixture_database, tmp_path)
    respx.get(URL).mock(return_value=httpx.Response(302, headers={"location": ASSET}))
    asset = respx.get(ASSET).mock(return_value=httpx.Response(200, content=bundle))
    target = materialize(cfg)
    assert target == tmp_path / cfg.compressed_sha256
    identity = json.loads((target / "identity.json").read_text())
    assert identity["release_tag"] == cfg.release_tag
    assert materialize(cfg) == target and asset.call_count == 1  # second run: no download

    path, actual = open_verified(cfg)
    assert path == target / "mitomap.sqlite"
    assert actual == {"release_tag": cfg.release_tag, "digest": f"sha256:{cfg.compressed_sha256}"}


@respx.mock
def test_digest_mismatch_is_refused(fixture_database: Path, tmp_path: Path) -> None:
    cfg, bundle = _config(fixture_database, tmp_path, compressed_sha256="1" * 64)
    respx.get(URL).mock(return_value=httpx.Response(200, content=bundle))
    with pytest.raises(DataUnavailableError):
        materialize(cfg)
    assert not any(tmp_path.iterdir())


@respx.mock
def test_redirect_to_unapproved_host_is_refused(fixture_database: Path, tmp_path: Path) -> None:
    cfg, _ = _config(fixture_database, tmp_path)
    respx.get(URL).mock(
        return_value=httpx.Response(302, headers={"location": "https://evil.test/x"})
    )
    with pytest.raises(DataUnavailableError):
        materialize(cfg)


@respx.mock
def test_oversized_bundle_is_refused(fixture_database: Path, tmp_path: Path) -> None:
    cfg, bundle = _config(fixture_database, tmp_path, max_compressed_bytes=10)
    respx.get(URL).mock(return_value=httpx.Response(200, content=bundle))
    with pytest.raises(DataUnavailableError):
        materialize(cfg)


def test_open_verified_rejects_tampered_database(fixture_database: Path, tmp_path: Path) -> None:
    cfg, _ = _config(fixture_database, tmp_path)
    target = tmp_path / cfg.compressed_sha256
    target.mkdir()
    (target / "mitomap.sqlite").write_bytes(fixture_database.read_bytes() + b"x")
    (target / "identity.json").write_text(
        json.dumps(
            {
                "release_tag": cfg.release_tag,
                "compressed_sha256": cfg.compressed_sha256,
                "expanded_sha256": cfg.expanded_sha256,
            }
        )
    )
    with pytest.raises(DataUnavailableError):
        open_verified(cfg)


def test_open_verified_missing_is_unavailable(fixture_database: Path, tmp_path: Path) -> None:
    cfg, _ = _config(fixture_database, tmp_path)
    with pytest.raises(DataUnavailableError):
        open_verified(cfg)
