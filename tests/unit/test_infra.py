"""Logging and the lazily opened, verified repository singleton."""

from __future__ import annotations

from pathlib import Path

import pytest

import mitomap_link.mcp.service_adapters as adapters
from mitomap_link.exceptions import DataUnavailableError
from mitomap_link.logging_config import configure_logging


def test_configure_logging_returns_logger() -> None:
    logger = configure_logging()
    assert logger is not None
    logger.info("test event", k="v")


async def test_local_database_is_opened_and_cached(
    monkeypatch: pytest.MonkeyPatch, fixture_database: Path
) -> None:
    adapters.set_repository(None)
    monkeypatch.setattr(adapters.settings.data, "local_database", fixture_database)
    try:
        first = await adapters.get_repository()
        assert await adapters.get_repository() is first
        assert adapters.peek_repository() is first
        assert adapters.observed_identity() is None  # development mode proves no release
    finally:
        adapters.set_repository(None)


async def test_unmaterialized_release_is_unavailable_and_not_cached(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fixture_database: Path
) -> None:
    adapters.set_repository(None)
    monkeypatch.setattr(adapters.settings.data, "local_database", None)
    monkeypatch.setattr(adapters.settings.data, "reference_root", tmp_path)
    with pytest.raises(DataUnavailableError):
        await adapters.get_repository()
    assert adapters.peek_repository() is None
    monkeypatch.setattr(adapters.settings.data, "local_database", fixture_database)
    try:
        assert await adapters.get_repository() is not None
    finally:
        adapters.set_repository(None)
