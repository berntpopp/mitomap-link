"""The derived SQLite snapshot built from the dump excerpt."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from mitomap_link.ingest.build import SourceInfo, build_database

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mitomap.dump.excerpt.sql"
SOURCE = SourceInfo(
    url="https://mitomap.org/downloads/mitomap.dump.sql.gz",
    sha256="0" * 64,
    size=1,
    last_modified="Wed, 11 Nov 2026 08:01:01 GMT",
)


def _build(tmp_path: Path, name: str = "mitomap.sqlite") -> Path:
    out = tmp_path / name
    with FIXTURE.open(encoding="utf-8") as fh:
        build_database(fh, out, SOURCE)
    return out


@pytest.fixture
def db(tmp_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(_build(tmp_path))
    conn.row_factory = sqlite3.Row
    return conn


def test_rna_mutation_keeps_mitomap_fields_verbatim(db: sqlite3.Connection) -> None:
    row = db.execute("SELECT * FROM variant WHERE position=3243 AND alt='G'").fetchone()
    assert row["kind"] == "mutation_rna"
    assert row["locus"] == "MT-TL1"
    assert row["allele"] == "A3243G"
    assert row["hgvs"] == "m.3243A>G"
    assert row["status"] == "Cfrm [P]"
    assert row["homoplasmy"] == "-" and row["heteroplasmy"] == "+"
    assert row["rna"] == "tRNA Leu (UUR)"
    assert row["gb_fl_count"] == 10 and row["gb_cr_count"] == 0
    assert "MELAS" in row["disease"]


def test_polymorphism_has_no_disease_and_derived_locus(db: sqlite3.Connection) -> None:
    row = db.execute("SELECT * FROM variant WHERE position=73 AND alt='G'").fetchone()
    assert row["kind"] == "polymorphism"
    assert row["disease"] is None and row["status"] is None
    assert row["locus"] == "MT-CR" and row["locus_source"] == "derived_from_coordinates"
    assert row["gb_fl_count"] > 1000


def test_dot_placeholders_become_null(db: sqlite3.Connection) -> None:
    row = db.execute("SELECT * FROM variant WHERE allele='m.5133_5134del'").fetchone()
    assert row["hgvs"] == "m.5133_5134del"
    assert row["alt"] == ":"


def test_references_link_to_pmids(db: sqlite3.Connection) -> None:
    pmids = [
        r[0]
        for r in db.execute(
            "SELECT pmid FROM reference r JOIN variant_reference ON r.id=reference_id "
            "JOIN variant v ON v.id=variant_id WHERE v.position=11778"
        )
    ]
    assert pmids and all(p is None or p.isdigit() for p in pmids)


def test_rcrs_bases_and_meta(db: sqlite3.Connection) -> None:
    assert db.execute("SELECT base FROM rcrs_base WHERE position=3243").fetchone()[0] == "A"
    meta = dict(db.execute("SELECT key, value FROM meta").fetchall())
    assert meta["source_last_modified"] == SOURCE.last_modified
    assert meta["genbank_full_length_total"] == "66775"
    assert meta["genbank_control_region_total"] == "81796"
    assert meta["schema_version"] == "1"


def test_build_is_byte_deterministic(tmp_path: Path) -> None:
    assert _build(tmp_path, "a.sqlite").read_bytes() == _build(tmp_path, "b.sqlite").read_bytes()


def test_submitter_contact_tables_are_never_read() -> None:
    from mitomap_link.ingest.build import TABLES

    assert not {t for t in TABLES if t == "unpublished" or t.startswith("submitted_variant")}
