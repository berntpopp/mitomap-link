"""mitomap-link: an MCP/API server for MITOMAP mitochondrial DNA variants."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mitomap-link")
except PackageNotFoundError:  # pragma: no cover - source tree without install
    __version__ = "0.0.0"

__all__ = ["__version__"]
