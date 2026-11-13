"""MCP contract-hardening v1 regression guards (issue #26 + fleet-four).

Locks the four fleet-wide contract fixes at the FastMCP-facade boundary:

* every error envelope carries the protocol ``isError: true`` flag (not just
  ``success: false``), so a client branching on ``isError`` sees the failure;
* ``error_code`` stays inside the closed six-value enum;
* a mistyped argument names the TYPE, not a phantom range (D5).
"""

from __future__ import annotations

from typing import Any

import pytest

# The exact six-value error_code enum (Response-Envelope Standard v1).
ERROR_CODES = {
    "invalid_input",
    "not_found",
    "ambiguous_query",
    "upstream_unavailable",
    "rate_limited",
    "internal",
}


@pytest.mark.parametrize(
    ("tool", "args"),
    [
        ("get_variant", {"variant": "NC_001807.4:m.3243A>G"}),  # invalid_input (reference)
        ("get_variant", {"nope": "x"}),  # invalid_input (unknown arg)
        ("get_variant", {"variant": "m.3243A>G", "response_mode": "huge"}),  # enum
        ("search_variants", {"limit": "ten"}),  # invalid_input (bad type)
        ("search_variants", {"limit": 0}),  # invalid_input (range)
        ("search_variants", {"locus": "MT-NOPE"}),  # invalid_input (vocabulary)
        ("get_variant", {}),  # invalid_input (missing variant)
    ],
)
async def test_every_error_sets_is_error_and_a_canon_code(
    facade: Any, structured: Any, tool: str, args: dict[str, Any]
) -> None:
    result = await facade.call_tool(tool, args)
    payload = structured(result)
    assert payload["success"] is False
    # THE fleet fix: a returned error envelope MUST set the protocol isError flag.
    assert result.is_error is True, f"{tool} error envelope did not set isError:true"
    assert payload["error_code"] in ERROR_CODES


async def test_success_call_is_not_flagged_as_error(facade: Any, structured: Any) -> None:
    result = await facade.call_tool("get_variant", {"variant": "m.3243A>G"})
    assert result.is_error is False
    assert structured(result)["success"] is True


async def test_mistyped_limit_names_the_type_not_a_range(facade: Any, structured: Any) -> None:
    """D5: limit='ten' is a TYPE error ('must be an integer'), not a range violation."""
    payload = structured(await facade.call_tool("search_variants", {"limit": "ten"}))
    assert payload["error_code"] == "invalid_input"
    assert payload["field"] == "limit"
    assert "integer" in payload["message"]
    assert "between" not in payload["message"]


async def test_full_adds_fields_over_compact(facade: Any, structured: Any) -> None:
    """compact and full are not identical for get_variant."""
    args = {"variant": "m.11778G>A"}
    compact = structured(await facade.call_tool("get_variant", args))
    full = structured(await facade.call_tool("get_variant", {**args, "response_mode": "full"}))
    record = next(r for r in full["records"] if r["references"])
    assert "references" not in compact["records"][0]
    assert set(record) > set(compact["records"][0])
