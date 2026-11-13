"""Build the compact, deterministic SQLite snapshot from the MITOMAP dump.

Only the disease-mutation, polymorphism, reference and locus tables are read (the dump
also carries submitter contact data, which is never touched). Values are kept as
MITOMAP states them; ``.``/empty placeholders become NULL. No wall-clock value enters
the database, so one dump + one toolchain always yields the same bytes.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from mitomap_link.ingest.dump import Row, read_copy_tables

SCHEMA_VERSION = "1"
TABLES = frozenset(
    {
        "mmutation",
        "rtmutation",
        "polymorphism",
        "mmutation_reference",
        "rtmutation_reference",
        "polymorphism_reference",
        "reference",
        "locus",
        "variants_count",
        "summary",
        "edit_date",
    }
)
_KINDS = {
    "mmutation": "mutation_coding_control",
    "rtmutation": "mutation_rna",
    "polymorphism": "polymorphism",
}
_GENE_LOCUS_TYPES = {"m", "r", "t"}
MT_LENGTH = 16569

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE variant (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    position INTEGER NOT NULL,
    ref TEXT,
    alt TEXT,
    hgvs TEXT,
    allele TEXT,
    locus TEXT,
    locus_source TEXT,
    disease TEXT,
    aa_change TEXT,
    rna TEXT,
    homoplasmy TEXT,
    heteroplasmy TEXT,
    status TEXT,
    status_date TEXT,
    gb_fl_count INTEGER,
    gb_cr_count INTEGER
) WITHOUT ROWID;
CREATE INDEX variant_position ON variant (position);
CREATE INDEX variant_locus ON variant (locus);
CREATE INDEX variant_allele ON variant (allele);
CREATE TABLE reference (
    id INTEGER PRIMARY KEY, pmid TEXT, year INTEGER, title TEXT, journal TEXT
);
CREATE TABLE variant_reference (
    variant_id TEXT NOT NULL, reference_id INTEGER NOT NULL,
    PRIMARY KEY (variant_id, reference_id)
) WITHOUT ROWID;
CREATE TABLE rcrs_base (position INTEGER PRIMARY KEY, base TEXT NOT NULL);
CREATE TABLE locus (
    name TEXT PRIMARY KEY, start INTEGER, end INTEGER, strand TEXT, type TEXT, product TEXT
) WITHOUT ROWID;
"""


@dataclass(frozen=True)
class SourceInfo:
    """Identity of the one downloaded upstream dump."""

    url: str
    sha256: str
    size: int
    last_modified: str


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return None if value in ("", ".") else value


def _int(value: str | None) -> int | None:
    value = _clean(value)
    return int(value) if value is not None and value.lstrip("-").isdigit() else None


def _covers(locus: Row, position: int) -> bool:
    start, end = _int(locus["starting"]), _int(locus["ending"])
    if start is None or end is None:
        return False
    return start <= position <= end if start <= end else position >= start or position <= end


def _derived_locus(loci: list[Row], position: int) -> str | None:
    genes = [
        loc for loc in loci if loc["type"] in _GENE_LOCUS_TYPES and _covers(loc, position)
    ]
    if genes:
        return "/".join(str(loc["name"]) for loc in sorted(genes, key=lambda r: _int(r["starting"]) or 0))
    control = next((loc for loc in loci if loc["name"] == "MT-CR"), None)
    return "MT-CR" if control is not None and _covers(control, position) else None


def _hgvs(position: int, ref: str | None, alt: str | None, allele: str | None) -> str | None:
    if allele is not None and allele.startswith("m."):
        return allele
    if ref and alt and len(ref) == len(alt) == 1 and ref in "ACGT" and alt in "ACGT":
        return f"m.{position}{ref}>{alt}"
    return None


def _variant_rows(tables: dict[str, list[Row]]) -> list[tuple[object, ...]]:
    counts = {
        (_int(r["tpos"]), r["tnt"], r["qnt"]): (_int(r["fl_count"]), _int(r["cr_count"]))
        for r in tables["variants_count"]
    }
    loci = tables["locus"]
    rows: list[tuple[object, ...]] = []
    for table, kind in _KINDS.items():
        for r in tables[table]:
            position = _int(r["position"])
            if position is None:
                continue
            ref, alt = _clean(r["refna"]), _clean(r["regna"])
            allele = _clean(r.get("allele"))
            locus = _clean(r.get("locus"))
            source = "mitomap_record" if locus else None
            if locus is None:
                locus = _derived_locus(loci, position)
                source = "derived_from_coordinates" if locus else None
            fl, cr = counts.get((position, ref, alt), (None, None))
            rows.append(
                (
                    f"{table}:{r['id']}",
                    kind,
                    position,
                    ref,
                    alt,
                    _hgvs(position, ref, alt, allele),
                    allele,
                    locus,
                    source,
                    _clean(r.get("dz")),
                    _clean(r.get("aa") or r.get("aachange")),
                    _clean(r.get("rna")),
                    _clean(r.get("homo")),
                    _clean(r.get("hetero")),
                    _clean(r.get("status")),
                    _clean(r.get("cfrm_date")),
                    fl,
                    cr,
                )
            )
    return sorted(rows, key=lambda row: str(row[0]))


def _rcrs_bases(tables: dict[str, list[Row]]) -> list[tuple[int, str]]:
    """rCRS bases implied by single-base substitutions; positions with conflicts are dropped."""
    seen: dict[int, set[str]] = {}
    observations = [(r["position"], r["refna"], r["regna"]) for t in _KINDS for r in tables[t]]
    observations += [(r["tpos"], r["tnt"], r["qnt"]) for r in tables["variants_count"]]
    for position, ref, alt in observations:
        pos = _int(position)
        if pos and ref in ("A", "C", "G", "T") and alt in ("A", "C", "G", "T"):
            seen.setdefault(pos, set()).add(str(ref))
    return sorted((pos, bases.pop()) for pos, bases in seen.items() if len(bases) == 1)


def _references(tables: dict[str, list[Row]]) -> tuple[list[tuple[object, ...]], list[tuple[str, int]]]:
    links: set[tuple[str, int]] = set()
    for table in _KINDS:
        key = f"{table}_id"
        for r in tables[f"{table}_reference"]:
            ref_id = _int(r["reference_id"])
            if ref_id is not None and r[key] is not None:
                links.add((f"{table}:{r[key]}", ref_id))
    used = {ref_id for _, ref_id in links}
    refs = []
    for r in tables["reference"]:
        ref_id = _int(r["id"])
        if ref_id not in used:
            continue
        nlmid = _clean(r["nlmid"])
        pmid = nlmid if nlmid is not None and nlmid.isdigit() else None
        refs.append((ref_id, pmid, _int(r["date"]), _clean(r["title"]), _clean(r["publication"])))
    return sorted(refs, key=lambda row: int(str(row[0]))), sorted(links)


def _meta(tables: dict[str, list[Row]], source: SourceInfo) -> list[tuple[str, str]]:
    summary = {r["name"]: r["count"] for r in tables["summary"]}
    edits = {r["table_name"]: r["date"] for r in tables["edit_date"]}
    meta = {
        "schema_version": SCHEMA_VERSION,
        "source_url": source.url,
        "source_sha256": source.sha256,
        "source_size": str(source.size),
        "source_last_modified": source.last_modified,
        "genbank_full_length_total": summary.get("genbank"),
        "genbank_control_region_total": summary.get("gbcontrol"),
        "edited_coding_control_mutations": edits.get("mMut"),
        "edited_rna_mutations": edits.get("rtMut"),
        "edited_polymorphisms": edits.get("polymorph"),
        "edited_references": edits.get("ref"),
    }
    return sorted((k, v) for k, v in meta.items() if v is not None)


def build_database(lines: Iterable[str], out: Path, source: SourceInfo) -> dict[str, int]:
    """Write the snapshot to ``out`` (replaced if present) and return record counts."""
    tables = read_copy_tables(lines, TABLES)
    variants = _variant_rows(tables)
    references, links = _references(tables)
    variant_ids = {str(row[0]) for row in variants}
    links = [link for link in links if link[0] in variant_ids]
    loci = sorted(
        (
            str(r["name"]),
            _int(r["starting"]),
            _int(r["ending"]),
            _clean(r["strand"]),
            _clean(r["type"]),
            _clean(r["product"]),
        )
        for r in tables["locus"]
        if r["name"]
    )
    out.unlink(missing_ok=True)
    conn = sqlite3.connect(out)
    try:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO meta VALUES (?, ?)", _meta(tables, source))
        conn.executemany(f"INSERT INTO variant VALUES ({', '.join('?' * 18)})", variants)
        conn.executemany("INSERT INTO reference VALUES (?, ?, ?, ?, ?)", references)
        conn.executemany("INSERT INTO variant_reference VALUES (?, ?)", links)
        conn.executemany("INSERT INTO rcrs_base VALUES (?, ?)", _rcrs_bases(tables))
        conn.executemany("INSERT INTO locus VALUES (?, ?, ?, ?, ?, ?)", loci)
        conn.commit()
        conn.execute("VACUUM")
    finally:
        conn.close()
    return {
        "variants": len(variants),
        "disease_mutations": sum(1 for v in variants if v[1] != "polymorphism"),
        "polymorphisms": sum(1 for v in variants if v[1] == "polymorphism"),
        "references": len(references),
    }
