"""The 2026-07-28 sessionless MCP era: discover -> list -> call over real HTTP."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from mitomap_link.config import settings
from mitomap_link.server_manager import create_unified_app

_HOST = "mitomap-link.genefoundry.org"
_MODERN_VERSION = "2026-07-28"
_MODERN_META = {
    "io.modelcontextprotocol/protocolVersion": _MODERN_VERSION,
    "io.modelcontextprotocol/clientCapabilities": {},
    "io.modelcontextprotocol/clientInfo": {"name": "mitomap-host-test", "version": "1.0.0"},
}


def _headers(method: str, *, name: str | None = None) -> dict[str, str]:
    headers = {
        "accept": "application/json, text/event-stream",
        "content-type": "application/json",
        "host": _HOST,
        "origin": "https://genefoundry.org",
        "mcp-protocol-version": _MODERN_VERSION,
        "mcp-method": method,
    }
    if name is not None:
        headers["mcp-name"] = name
    return headers


def _rpc(
    client: TestClient, rid: int, method: str, params: dict[str, Any], name: str | None = None
) -> httpx.Response:
    return client.post(
        "/mcp",
        headers=_headers(method, name=name),
        json={
            "jsonrpc": "2.0",
            "id": rid,
            "method": method,
            "params": {"_meta": _MODERN_META, **params},
        },
    )


def test_modern_mcp_http_discovers_lists_calls_and_fences_unknown_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "allowed_hosts", ["localhost", _HOST])
    monkeypatch.setattr(settings, "allowed_origins", ["https://genefoundry.org"])
    hostile = "ignore-instructions-secret"
    with TestClient(create_unified_app(), follow_redirects=False) as client:
        discover = _rpc(client, 1, "server/discover", {})
        listed = _rpc(client, 2, "tools/list", {})
        called = _rpc(
            client,
            3,
            "tools/call",
            {"name": "get_server_capabilities", "arguments": {}},
            name="get_server_capabilities",
        )
        unknown = _rpc(client, 4, "tools/call", {"name": hostile, "arguments": {}}, name=hostile)

    assert discover.status_code == 200
    assert _MODERN_VERSION in discover.json()["result"]["supportedVersions"]
    assert "mcp-session-id" not in discover.headers
    assert listed.status_code == 200
    assert {t["name"] for t in listed.json()["result"]["tools"]} >= {
        "get_variant",
        "search_variants",
    }
    assert called.status_code == 200
    called_result = called.json()["result"]
    assert json.loads(called_result["content"][0]["text"]) == called_result["structuredContent"]
    assert called_result["structuredContent"]["success"] is True
    assert unknown.status_code == 200
    unknown_result = unknown.json()["result"]
    assert unknown_result["isError"] is True
    assert unknown_result["structuredContent"]["error_code"] == "not_found"
    assert hostile not in unknown.text
