"""The code pin, the fleet release contract and the deploy overlays agree."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from mitomap_link.store import pin

ROOT = Path(__file__).resolve().parents[2]
RELEASE = json.loads((ROOT / "container-release.json").read_text(encoding="utf-8"))


def test_container_release_data_matches_pin() -> None:
    data = RELEASE["data"]
    assert data["mode"] == "external-reference"
    assert data["release_tag"] == pin.RELEASE_TAG
    assert data["digest"] == f"sha256:{pin.COMPRESSED_SHA256}"
    assert f"data-mitomap-{pin.EXPANDED_SHA256[:16]}" == pin.RELEASE_TAG
    assert pin.RELEASE_TAG in pin.BUNDLE_URL
    assert RELEASE["data_identity_contract"] == "runtime-v1"
    assert RELEASE["definitions"]["contract"] == "data-bound"


def test_every_overlay_runs_the_init_before_the_app() -> None:
    for name in ("docker-compose.yml", "docker-compose.npm.yml"):
        services = yaml.safe_load((ROOT / "docker" / name).read_text())["services"]
        init = services["mitomap-data-init"]
        assert init["command"] == ["materialize"] and init["restart"] == "no"
        app = next(s for k, s in services.items() if k != "mitomap-data-init")
        assert app["depends_on"]["mitomap-data-init"]["condition"] == (
            "service_completed_successfully"
        )
        assert any(str(v).endswith(":/data:ro") for v in app["volumes"])
