"""The pg_dump reader: COPY blocks are parsed as data, never executed."""

from __future__ import annotations

from pathlib import Path

import pytest

from mitomap_link.ingest.dump import DumpFormatError, read_copy_tables, unescape

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mitomap.dump.excerpt.sql"


def _read(text: str, *tables: str) -> dict[str, list[dict[str, str | None]]]:
    return read_copy_tables(text.splitlines(keepends=True), frozenset(tables))


def test_reads_only_requested_tables_as_dicts() -> None:
    with FIXTURE.open(encoding="utf-8") as fh:
        tables = read_copy_tables(fh, frozenset({"rtmutation", "summary"}))
    assert set(tables) == {"rtmutation", "summary"}
    melas = next(r for r in tables["rtmutation"] if r["allele"] == "A3243G")
    assert melas["locus"] == "MT-TL1"
    assert melas["status"] == "Cfrm [P]"
    assert melas["position"] == "3243"
    assert {r["name"]: r["count"] for r in tables["summary"]}["genbank"] == "66775"


def test_null_marker_becomes_none_and_escapes_are_decoded() -> None:
    assert unescape("\\N") is None
    assert unescape("a\\tb\\\\c\\nd") == "a\tb\\c\nd"
    assert unescape("\\101") == "A"
    assert unescape("\\x41") == "A"


def test_sql_statements_are_ignored_not_interpreted() -> None:
    text = (
        "COPY mitomap.evil (x) TO PROGRAM 'rm -rf /';\n"
        "DROP TABLE mitomap.summary;\n"
        "COPY mitomap.summary (name, count) FROM stdin;\n"
        "genbank\t1\n"
        "\\.\n"
    )
    assert _read(text, "summary") == {"summary": [{"name": "genbank", "count": "1"}]}


def test_missing_table_is_an_error() -> None:
    with pytest.raises(DumpFormatError, match="locus"):
        _read("SET x = 1;\n", "locus")


def test_column_count_mismatch_is_an_error() -> None:
    text = "COPY mitomap.summary (name, count) FROM stdin;\ngenbank\n\\.\n"
    with pytest.raises(DumpFormatError):
        _read(text, "summary")


def test_unterminated_copy_block_is_an_error() -> None:
    with pytest.raises(DumpFormatError):
        _read("COPY mitomap.summary (name, count) FROM stdin;\ngenbank\t1\n", "summary")
