"""Response-Envelope Standard v1.2: every data tool's success validates against the schema.

The schema is vendored from berntpopp/genefoundry-envelope, tag v1.2.0
(https://raw.githubusercontent.com/berntpopp/genefoundry-envelope/v1.2.0/envelope-v1.2.schema.json).
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from mitomap_link.store.pin import RETRIEVED_AT

SCHEMA_PATH = Path(__file__).with_name("envelope-v1.2.schema.json")
SCHEMA_SHA256 = "c3c47e20d7dd189aac2568fc963b5514d7a5ac2c3e5f21d126f42c96d1ad1ae3"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

# One successful call per data tool. get_server_capabilities and get_diagnostics are
# ops/meta tools and outside the v1.2 rule.
CALLS: dict[str, dict[str, Any]] = {
    "get_variant": {"variant": "MT-3243-A-G"},
    "search_variants": {"locus": "MT-ATP6"},
}
OPS_TOOLS = {"get_server_capabilities", "get_diagnostics"}


def test_vendored_schema_is_the_v1_2_0_release() -> None:
    assert sha256(SCHEMA_PATH.read_bytes()).hexdigest() == SCHEMA_SHA256


async def test_every_data_tool_is_covered(facade: Any) -> None:
    registered = {tool.name for tool in await facade.list_tools()}
    assert registered - OPS_TOOLS == set(CALLS)


@pytest.mark.parametrize("tool", sorted(CALLS))
async def test_success_validates_and_carries_provenance(
    facade: Any, structured: Any, tool: str
) -> None:
    envelope = structured(await facade.call_tool(tool, CALLS[tool]))
    assert envelope["success"] is True
    jsonschema.validate(envelope, SCHEMA)
    meta = envelope["_meta"]
    assert meta["source"] == "mitomap"
    assert meta["data_version"].startswith("mitomap-dump@")
    # The dump's download time, not the time of this call.
    assert meta["retrieved_at"] == RETRIEVED_AT


async def test_error_envelope_validates_too(facade: Any, structured: Any) -> None:
    envelope = structured(await facade.call_tool("get_variant", {"variant": "rs199474657"}))
    assert envelope["success"] is False
    jsonschema.validate(envelope, SCHEMA)
