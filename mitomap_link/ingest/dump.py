"""Read table rows out of MITOMAP's plain-text PostgreSQL dump without a database.

The dump is untrusted input. It is never executed or restored: only the data lines of
``COPY mitomap.<table> (<cols>) FROM stdin;`` blocks for an explicit allowlist of tables
are decoded (PostgreSQL text COPY format); every other line, SQL statement or
psql meta-command is skipped unread.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

_COPY_RE = re.compile(r"^COPY mitomap\.([a-z_][a-z0-9_]*) \(([^()]*)\) FROM stdin;\n?$")
_END = "\\."
_ESCAPES = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\"}
_ESCAPE_RE = re.compile(r"\\(x[0-9A-Fa-f]{1,2}|[0-7]{1,3}|.)")

Row = dict[str, str | None]


class DumpFormatError(ValueError):
    """The dump does not have the shape the builder relies on."""


def unescape(field: str) -> str | None:
    """Decode one PostgreSQL text-format COPY field (``\\N`` is NULL)."""
    if field == "\\N":
        return None

    def _sub(match: re.Match[str]) -> str:
        token = match.group(1)
        if token[0] == "x" and len(token) > 1:
            return chr(int(token[1:], 16))
        if token.isdigit():
            return chr(int(token, 8))
        return _ESCAPES.get(token, token)

    return _ESCAPE_RE.sub(_sub, field)


def read_copy_tables(lines: Iterable[str], wanted: frozenset[str]) -> dict[str, list[Row]]:
    """Return ``{table: [row dict]}`` for every wanted table; all must be present."""
    tables: dict[str, list[Row]] = {}
    current: str | None = None
    columns: list[str] = []
    for line in lines:
        if current is None:
            match = _COPY_RE.match(line)
            if match and match.group(1) in wanted:
                current = match.group(1)
                if current in tables:
                    raise DumpFormatError(f"table {current} appears twice")
                columns = [c.strip().strip('"') for c in match.group(2).split(",")]
                tables[current] = []
            continue
        body = line.rstrip("\n")
        if body == _END:
            current = None
            continue
        fields = body.split("\t")
        if len(fields) != len(columns):
            raise DumpFormatError(f"table {current}: expected {len(columns)} columns")
        tables[current].append(dict(zip(columns, map(unescape, fields), strict=True)))
    if current is not None:
        raise DumpFormatError(f"table {current}: COPY block is not terminated")
    missing = sorted(wanted - tables.keys())
    if missing:
        raise DumpFormatError(f"tables missing from dump: {', '.join(missing)}")
    return tables
