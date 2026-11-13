"""The process-wide repository over the verified snapshot, opened lazily once.

A failed open is not cached, so a call made before the init container finished simply
retries. ``identity`` is the observed release identity (None in local development mode).
"""

from __future__ import annotations

import asyncio

from mitomap_link.config import settings
from mitomap_link.store.identity import open_verified
from mitomap_link.store.repository import Repository

_repository: Repository | None = None
_identity: dict[str, str] | None = None
_lock = asyncio.Lock()


def _open() -> tuple[Repository, dict[str, str] | None]:
    cfg = settings.data
    if cfg.local_database is not None:
        return Repository(cfg.local_database), None
    path, identity = open_verified(cfg)
    return Repository(path), identity


async def get_repository() -> Repository:
    """Return the verified repository (raises DataUnavailableError until materialized)."""
    global _repository, _identity
    async with _lock:
        if _repository is None:
            opened, identity = await asyncio.to_thread(_open)
            _repository, _identity = opened, identity
            return opened
        return _repository


def peek_repository() -> Repository | None:
    """The repository if already open (never opens it)."""
    return _repository


def observed_identity() -> dict[str, str] | None:
    """The release identity verified when the repository was opened."""
    return _identity


def set_repository(repository: Repository | None, identity: dict[str, str] | None = None) -> None:
    """Override the singleton (used by tests)."""
    global _repository, _identity
    _repository, _identity = repository, identity
