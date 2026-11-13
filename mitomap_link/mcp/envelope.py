"""MCP envelope boundary: success/_meta injection and structured errors.

Tools return a plain dict; :func:`run_mcp_tool` injects ``success`` and ``_meta``
on success, and converts any exception into a structured error dict (returned,
never raised) so the LLM sees a typed failure rather than an opaque masked
message.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal, get_args

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from pydantic import ValidationError as PydanticValidationError

from mitomap_link.exceptions import (
    DataUnavailableError,
    InvalidInputError,
    NotFoundError,
)
from mitomap_link.mcp._sanitize import safe_field_name, sanitize_envelope, sanitize_message
from mitomap_link.mcp.next_commands import cmd, default_error_next_commands
from mitomap_link.safe_fields import safe_allowed_values

logger = logging.getLogger(__name__)

# Per-call _meta carries dynamic fields (tool, request_id, next_commands) plus
# the fleet-standard unsafe_for_clinical_use disclaimer, which per the
# GeneFoundry Response-Envelope Standard v1 (2026-07-03 fleet decision) must be
# stamped on EVERY tool response -- success and error, at all response_modes --
# not declared once via get_server_capabilities. Each data tool also stamps the
# CC BY recommended_citation and _meta.data_version itself.
_RETRYABLE = {"rate_limited", "upstream_unavailable"}
_UNSAFE_FOR_CLINICAL_USE = True


@dataclass
class McpErrorContext:
    """Per-call context so envelopes can name the failing tool and recovery."""

    tool_name: str
    fallback: dict[str, Any] | None = field(default=None)
    arguments: dict[str, Any] = field(default_factory=dict)


# The closed error_code enum (Response-Envelope Standard v1). Anything else is a
# violation, so codes entering the envelope are clamped to this set.
ErrorCode = Literal[
    "invalid_input",
    "not_found",
    "ambiguous_query",
    "upstream_unavailable",
    "rate_limited",
    "internal",
]
_ERROR_CODES: frozenset[str] = frozenset(get_args(ErrorCode))


def _clamp_error_code(code: str) -> str:
    """Clamp an arbitrary code to the closed enum; anything unknown is ``internal``."""
    return code if code in _ERROR_CODES else "internal"


class McpToolError(Exception):
    """Raised inside a tool body to emit a specific error code/message."""

    def __init__(self, *, error_code: ErrorCode, message: str) -> None:
        """Store an error code (clamped to the closed enum) and client-safe message."""
        super().__init__(message)
        self.error_code: str = _clamp_error_code(error_code)
        self.message = message


def _request_id() -> str:
    return uuid.uuid4().hex[:12]


# FIXED, error-code-specific public messages. The message NEVER interpolates the
# caller's query/identifier or an upstream value: those carry injection prose that
# survives code-point stripping (the deepest fleet-review lesson). The actionable
# detail travels in structured, server-authored fields (field / allowed_values /
# hint / candidates / next_commands); the raw exception text stays server-side.
# Keys are the closed error_code enum (Response-Envelope Standard v1): invalid_input,
# not_found, ambiguous_query, upstream_unavailable, rate_limited, internal. The local
# MITOMAP snapshot being unmaterialized/unverifiable maps onto upstream_unavailable
# (retryable: the next call re-attempts the load), not a bespoke code.
_PUBLIC_MESSAGE: dict[str, str] = {
    "not_found": "No matching MITOMAP record. Use search_variants to browse.",
    "ambiguous_query": "The request matched several MITOMAP records; pick one from candidates.",
    "invalid_input": "The request was invalid. See field / allowed_values / hint.",
    "rate_limited": "Rate limit hit. Retry shortly.",
    "upstream_unavailable": "The MITOMAP snapshot is temporarily unavailable. Retry shortly.",
    "internal": "An internal error occurred. The request was not completed.",
}

# Closed table of fixed, server-authored invalid_input messages, keyed by the
# exception's ``reason``. The exception's own text is never used; an unknown reason
# falls back to the generic message.
_INVALID_REASON_MESSAGE: dict[str, str] = {
    "unsupported_reference": "Only the rCRS mitochondrial reference (NC_012920.1, alias "
    "J01415.2) is supported; allowed_values lists the accepted accessions.",
    "reference_mismatch": "The reference base does not match rCRS (NC_012920.1) at this "
    "position; allowed_values holds the rCRS base.",
    "unrecognized_notation": "Unrecognized mtDNA variant notation. Use rCRS HGVS such as "
    "m.3243A>G, MT-3243-A-G or chrM:3243 A>G (indels: m.5133_5134del).",
    "dbsnp_id": "dbSNP rs ids are not indexed by MITOMAP; resolve the rs id to an rCRS "
    "allele (e.g. m.3243A>G) first.",
    "position_out_of_range": "rCRS positions run 1-16569.",
    "invalid_substitution": "ref and alt must differ and have equal length; write indels in "
    "HGVS (m.5133_5134del).",
    "unknown_locus": "Unknown MITOMAP locus; use an MT- gene/region symbol such as MT-TL1 or "
    "MT-ATP6 (see did_you_mean).",
    "inverted_range": "position_start must not exceed position_end.",
}

# Fixed, server-authored recovery hint for invalid_input. The exception's own
# ``hint`` is NOT surfaced (it could carry copied prose); ``field`` +
# ``allowed_values`` already carry the validated, actionable detail.
_INVALID_INPUT_HINT = "Correct the offending argument (see field and allowed_values), then retry."


def _classify(exc: BaseException) -> tuple[str, str]:
    """Return ``(error_code, fixed_public_message)`` for an exception.

    Only ``McpToolError`` supplies its own message (server-authored, raised inside
    a tool body); every other class maps to a FIXED public message so no caller
    input or upstream value is ever echoed into a caller-visible string.
    """
    if isinstance(exc, McpToolError):
        return _clamp_error_code(exc.error_code), exc.message
    if isinstance(exc, InvalidInputError) and exc.reason in _INVALID_REASON_MESSAGE:
        return "invalid_input", _INVALID_REASON_MESSAGE[exc.reason]
    if isinstance(exc, NotFoundError):
        code = "not_found"
    elif isinstance(exc, InvalidInputError | PydanticValidationError):
        code = "invalid_input"
    elif isinstance(exc, DataUnavailableError):
        code = "upstream_unavailable"
    else:
        code = "internal"
    return code, _PUBLIC_MESSAGE[code]


def _recovery_action(error_code: str) -> str:
    if error_code in _RETRYABLE:
        return "retry_backoff"
    if error_code in {"invalid_input", "not_found", "ambiguous_query"}:
        return "reformulate_input"
    return "switch_tool"


def _error_envelope(exc: BaseException, context: McpErrorContext) -> dict[str, Any]:
    error_code, message = _classify(exc)
    envelope: dict[str, Any] = {
        "success": False,
        "error_code": error_code,
        # Defensive: no forbidden code points reach the caller, whatever the path
        # (McpToolError / fixed classified strings included).
        "message": sanitize_message(message),
        "retryable": error_code in _RETRYABLE,
        "recovery_action": _recovery_action(error_code),
        "_meta": {
            "tool": context.tool_name,
            "request_id": _request_id(),
            "unsafe_for_clinical_use": _UNSAFE_FOR_CLINICAL_USE,
        },
    }
    # DEFINITIVE RULE: never copy an exception attribute verbatim into a caller-
    # visible field. Each is rebuilt from a validated identifier, a closed enum, or
    # a fixed server string; non-conforming values are dropped. sanitize_envelope()
    # is only the final code-point backstop ON TOP of this.
    if isinstance(exc, InvalidInputError):
        if exc.field is not None:
            envelope["field"] = safe_field_name(exc.field)  # identifier or <redacted>
        if exc.allowed is not None:
            envelope["allowed_values"] = safe_allowed_values(exc.allowed)  # drop prose
        if exc.hint is not None:
            envelope["hint"] = _INVALID_INPUT_HINT  # fixed server string, not exc.hint
        if exc.did_you_mean is not None:
            # A suggestion drawn from a CLOSED server vocabulary; validated through the
            # allowed-value grammar (drops anything prose-like) before it is surfaced.
            suggestion = safe_allowed_values(exc.did_you_mean)
            if suggestion:
                envelope["did_you_mean"] = suggestion
    if context.fallback is not None:
        envelope["_meta"]["next_commands"] = [context.fallback]
    else:
        envelope["_meta"]["next_commands"] = default_error_next_commands(
            context.tool_name, error_code, context.arguments
        )
    # Final code-point backstop over EVERY string leaf (message, field,
    # allowed_values, hint, and
    # _meta.next_commands[*].arguments.*), whichever branch built them.
    return sanitize_envelope(envelope)


def build_arg_error_envelope(
    *,
    tool_name: str,
    loc: str,
    error_type: str,
    valid_params: list[str],
    signature: str,
    suggestion: str | None,
    constraints: tuple[list[str], str] | None = None,
) -> dict[str, Any]:
    """Standard invalid-input envelope for an argument-binding failure.

    When ``constraints`` is supplied the failure is an invalid *value* on a known
    argument, so ``allowed_values`` carries the valid range/enum (not the list of
    argument *names*) and the message states the constraint.
    """
    # ``loc`` is the caller-supplied argument NAME (attacker-influenceable for an
    # unexpected/unknown key). It is NEVER interpolated into the message -- it is
    # validated-or-redacted into the structured ``field`` key only. The message is
    # built solely from server-derived values: ``tool_name``, the server-computed
    # ``suggestion`` (always a real parameter name), ``signature``, and the
    # schema-derived constraint ``human`` phrase.
    safe_loc = safe_field_name(loc)
    dym = f" Did you mean `{suggestion}`?" if suggestion else ""
    if constraints is not None:
        allowed, human = constraints
        message = f"Invalid argument value for {tool_name}: {human}. See 'field'."
        allowed_values = allowed
    else:
        if error_type == "missing_argument":
            head = f"A required argument is missing for {tool_name}."
        elif error_type == "unexpected_keyword_argument":
            head = f"An unknown argument was supplied to {tool_name}."
        else:
            head = f"An argument value was invalid for {tool_name}."
        message = f"{head}{dym} See 'field'; valid names are in allowed_values."
        allowed_values = valid_params
    return sanitize_envelope(
        {
            "success": False,
            "error_code": "invalid_input",
            "message": sanitize_message(message),
            "retryable": False,
            "recovery_action": "reformulate_input",
            "field": safe_loc,
            "allowed_values": safe_allowed_values(allowed_values),
            "hint": signature,
            "_meta": {
                "tool": tool_name,
                "request_id": _request_id(),
                "next_commands": [cmd("get_server_capabilities")],
                "unsafe_for_clinical_use": _UNSAFE_FOR_CLINICAL_USE,
            },
        }
    )


async def run_mcp_tool(
    tool_name: str,
    call: Callable[[], Awaitable[dict[str, Any]]],
    *,
    context: McpErrorContext | None = None,
) -> dict[str, Any] | ToolResult:
    """Execute a tool body, returning the success dict or a structured error result.

    A success returns a plain dict (FastMCP wraps it, emitting ``structuredContent``).
    An error returns a ``ToolResult(is_error=True)`` carrying the SAME structured
    envelope plus a TextContent JSON mirror, so the protocol ``isError`` flag is set
    (Response-Envelope Standard v1: REQUIRED so a client surfaces the error to the
    model for self-correction) while the machine-readable envelope is preserved.
    """
    ctx = context or McpErrorContext(tool_name=tool_name)
    started = time.perf_counter()
    try:
        result = await call()
        if isinstance(result, dict):
            result.setdefault("success", True)
            existing_meta: dict[str, Any] = result.get("_meta") or {}
            result["_meta"] = {
                **existing_meta,
                "tool": tool_name,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
                "request_id": _request_id(),
                "unsafe_for_clinical_use": _UNSAFE_FOR_CLINICAL_USE,
            }
            # Code-point backstop over the WHOLE success payload too (curated data
            # is clean, so this is a no-op there; it strips any forbidden code point
            # from a caller-echoed correlation key such as a batch row's `query`).
            result = sanitize_envelope(result)
            # A tool body may RETURN an error envelope (success:false) rather than
            # raise; it must still set the protocol isError flag, so route it through
            # the same ToolResult chokepoint as the raise path.
            if result.get("success") is False:
                return _error_tool_result(result)
        return result
    except Exception as exc:  # broad catch is the error-boundary contract
        envelope = _error_envelope(exc, ctx)
        logger.warning(
            "mcp_tool_error tool=%s code=%s exc=%s",
            tool_name,
            envelope["error_code"],
            exc.__class__.__name__,
        )
        return _error_tool_result(envelope)


def _error_tool_result(envelope: dict[str, Any]) -> ToolResult:
    """Wrap a structured error envelope so the protocol ``isError`` flag is set."""
    return ToolResult(
        structured_content=envelope,
        content=[TextContent(type="text", text=json.dumps(envelope))],
        is_error=True,
    )
