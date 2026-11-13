"""Discovery tools: get_server_capabilities, get_diagnostics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import Field

from mitomap_link.config import settings
from mitomap_link.exceptions import DataUnavailableError
from mitomap_link.mcp.annotations import READ_ONLY_OPEN_WORLD
from mitomap_link.mcp.capabilities import collect_tool_signatures, project_capabilities
from mitomap_link.mcp.envelope import McpErrorContext, run_mcp_tool
from mitomap_link.mcp.next_commands import cmd
from mitomap_link.mcp.service_adapters import get_repository, observed_identity
from mitomap_link.store.identity import expected_identity

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register_discovery_tools(mcp: FastMCP) -> None:
    """Register discovery tools on a FastMCP instance."""

    @mcp.tool(
        name="get_server_capabilities",
        title="Get Server Capabilities",
        annotations=READ_ONLY_OPEN_WORLD,
        output_schema=None,
        tags={"discovery", "meta"},
        description=(
            "Return the mitomap-link discovery surface: tools with call signatures, "
            "argument aliases, response modes, accepted variant notations, status/plasmy/"
            "GenBank semantics, error codes, limits, data pin, license and citation. "
            "detail='full' adds the usage notes. "
            "Signature: get_server_capabilities(detail=)."
        ),
    )
    async def get_server_capabilities(
        detail: Annotated[
            Literal["summary", "full"],
            Field(description="summary (default) or full (adds usage notes)."),
        ] = "summary",
    ) -> dict[str, Any]:
        async def call() -> dict[str, Any]:
            return project_capabilities(detail, await collect_tool_signatures(mcp))

        return await run_mcp_tool(
            "get_server_capabilities",
            call,
            context=McpErrorContext("get_server_capabilities"),
        )

    @mcp.tool(
        name="get_diagnostics",
        title="Get Diagnostics",
        annotations=READ_ONLY_OPEN_WORLD,
        output_schema=None,
        tags={"discovery", "meta"},
        description=(
            "Report whether the pinned MITOMAP data release is materialized and verified: "
            "expected vs observed release tag and digest, upstream dump Last-Modified and "
            "SHA-256, MITOMAP edit dates and record counts. Use it to confirm the data "
            "version or diagnose an upstream_unavailable error. Signature: get_diagnostics()."
        ),
    )
    async def get_diagnostics() -> dict[str, Any]:
        async def call() -> dict[str, Any]:
            release = {"expected": expected_identity(settings.data), "observed": None}
            try:
                repo = await get_repository()
            except DataUnavailableError:
                return {
                    "data_available": False,
                    "release": release,
                    "_meta": {"next_commands": [cmd("get_server_capabilities")]},
                }
            release["observed"] = observed_identity()
            meta = repo.meta
            return {
                "data_available": True,
                "release": release,
                "local_development_database": settings.data.local_database is not None,
                "source": {
                    "url": meta.get("source_url"),
                    "sha256": meta.get("source_sha256"),
                    "size": meta.get("source_size"),
                    "last_modified": meta.get("source_last_modified"),
                },
                "mitomap_edit_dates": {
                    k.removeprefix("edited_"): v for k, v in meta.items() if k.startswith("edited_")
                },
                "record_counts": repo.counts(),
                "schema_version": meta.get("schema_version"),
                "_meta": {"next_commands": [cmd("get_variant", variant="m.3243A>G")]},
            }

        return await run_mcp_tool(
            "get_diagnostics", call, context=McpErrorContext("get_diagnostics")
        )
