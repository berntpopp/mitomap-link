"""MCP tool registration entry points."""

from __future__ import annotations

from mitomap_link.mcp.tools.discovery import register_discovery_tools
from mitomap_link.mcp.tools.variants import register_variant_tools

__all__ = ["register_discovery_tools", "register_variant_tools"]
