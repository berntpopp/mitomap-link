"""Shared fixtures: a snapshot built from the dump excerpt and a facade wired to it."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

DUMP_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mitomap.dump.excerpt.sql"


def _structured(result: Any) -> dict[str, Any]:
    """Read structured_content defensively (with TextContent JSON fallback)."""
    sc = result.structured_content
    if isinstance(sc, dict):
        return sc
    return json.loads(result.content[0].text)


@pytest.fixture
def structured() -> Any:
    """Expose the structured-content reader to tests."""
    return _structured


@pytest.fixture(scope="session")
def fixture_database(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The snapshot built from the checked-in dump excerpt."""
    from mitomap_link.ingest.build import SourceInfo, build_database

    out = tmp_path_factory.mktemp("db") / "mitomap.sqlite"
    with DUMP_FIXTURE.open(encoding="utf-8") as fh:
        build_database(fh, out, SourceInfo("https://mitomap.org/x", "0" * 64, 1, "fixture"))
    return out


@pytest.fixture
def repo(fixture_database: Path) -> Any:
    from mitomap_link.store.repository import Repository

    return Repository(fixture_database)


@pytest.fixture
def facade(fixture_database: Path) -> Any:
    """A FastMCP facade with the fixture snapshot injected; cleans up after."""
    from mitomap_link.mcp.facade import create_mitomap_mcp
    from mitomap_link.mcp.service_adapters import set_repository
    from mitomap_link.store.repository import Repository

    set_repository(Repository(fixture_database))
    mcp = create_mitomap_mcp()
    yield mcp
    set_repository(None)
