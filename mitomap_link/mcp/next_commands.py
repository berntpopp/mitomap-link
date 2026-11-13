"""Builders for `_meta.next_commands` entries: `{tool, arguments}` steps.

Only grammar-validated identifiers are echoed into a next_command; a free-form caller
value (which could carry injection prose) is never placed into one. Tools of sibling
GeneFoundry servers are named as the router exposes them (``gnomad_...``).
"""

from __future__ import annotations

import re
from typing import Any

_HGVS = re.compile(r"^m\.\d{1,5}(?:_\d{1,5})?[ACGT>a-z]{1,40}$")
_LOCUS = re.compile(r"^MT-[A-Z0-9]{1,12}$")
_GNOMAD_MITO = re.compile(r"^M-\d{1,5}-[ACGT]-[ACGT]$")


def cmd(tool: str, **arguments: Any) -> dict[str, Any]:
    """One ready-to-call next step."""
    return {"tool": tool, "arguments": arguments}


def is_hgvs(value: Any) -> bool:
    """True for a server-built rCRS HGVS string (safe to echo)."""
    return isinstance(value, str) and _HGVS.match(value) is not None


def default_error_next_commands(
    tool: str, error_code: str, arguments: dict[str, Any]
) -> list[dict[str, Any]]:
    """A sensible recovery step for any error lacking an explicit fallback."""
    del tool, arguments  # caller values are never echoed back
    if error_code == "upstream_unavailable":
        return [cmd("get_diagnostics")]
    return [cmd("get_server_capabilities")]


def after_variant(
    gnomad_id: str | None, loci: list[str], position: int, found: bool
) -> list[dict[str, Any]]:
    """After get_variant: population context in gnomAD, then neighbours in MITOMAP."""
    steps: list[dict[str, Any]] = []
    if gnomad_id is not None and _GNOMAD_MITO.match(gnomad_id):
        steps.append(cmd("gnomad_get_mitochondrial_variant", variant_id=gnomad_id))
    if not found:
        steps.append(
            cmd(
                "search_variants", position_start=position, position_end=position, record_type="any"
            )
        )
    steps += [cmd("search_variants", locus=locus) for locus in loci[:1] if _LOCUS.match(locus)]
    return steps or [cmd("get_server_capabilities")]


def after_search(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """After search_variants: open the top hit, or point home if empty."""
    if results and is_hgvs(results[0].get("hgvs")):
        return [cmd("get_variant", variant=results[0]["hgvs"])]
    return [cmd("get_server_capabilities")]
