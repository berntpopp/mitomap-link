"""Custom exceptions for mitomap-link.

``run_mcp_tool`` classifies each into a stable ``error_code`` (see
``mitomap_link.mcp.envelope``).
"""

from __future__ import annotations


class MitomapError(Exception):
    """Base exception for all mitomap-link data errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Store a human-readable message and optional HTTP status code."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        """Return the message (with status code when present)."""
        if self.status_code is not None:
            return f"[{self.status_code}] {self.message}"
        return self.message


class InvalidInputError(MitomapError):
    """A tool/service argument failed validation before any lookup ran."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        *,
        allowed: list[str] | None = None,
        hint: str | None = None,
        did_you_mean: list[str] | None = None,
    ) -> None:
        """Initialise with the offending field and optional recovery data.

        ``allowed``/``hint``/``did_you_mean`` surface as structured envelope keys; they
        are re-validated there and never copied as prose.
        """
        super().__init__(message)
        self.field = field
        self.allowed = allowed
        self.hint = hint
        self.did_you_mean = did_you_mean


class NotFoundError(MitomapError):
    """A lookup matched no MITOMAP record."""

    def __init__(self, message: str = "No matching MITOMAP record found.") -> None:
        """Initialise with a 404 status code."""
        super().__init__(message, status_code=404)


class AmbiguousQueryError(MitomapError):
    """A query matched several records and cannot be resolved unambiguously."""

    def __init__(self, message: str, *, candidates: list[dict[str, str]] | None = None) -> None:
        """Store the ambiguous candidates (``locus_id``/``gene``) for the envelope."""
        super().__init__(message)
        self.candidates = candidates or []


class DataUnavailableError(MitomapError):
    """The pinned MITOMAP snapshot could not be materialized or verified."""

    def __init__(self, message: str = "The MITOMAP snapshot is not available.") -> None:
        """Initialise with a 503 status code."""
        super().__init__(message, status_code=503)
