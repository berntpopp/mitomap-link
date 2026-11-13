"""Queries over the derived MITOMAP SQLite snapshot (opened read-only, immutable)."""

from __future__ import annotations

import difflib
import re
import sqlite3
from pathlib import Path
from typing import Any, Literal

from mitomap_link.exceptions import DataUnavailableError, InvalidInputError
from mitomap_link.variant_ids import VariantQuery

StatusCategory = Literal["reported", "confirmed", "conflicting_reports", "unclear"]
RecordType = Literal["disease_mutation", "polymorphism", "any"]
STATUS_PREFIX: dict[str, str] = {
    "reported": "Reported",
    "confirmed": "Cfrm",
    "conflicting_reports": "Conflicting",
    "unclear": "Unclear",
}
_REF_COUNT = "(SELECT COUNT(*) FROM variant_reference vr WHERE vr.variant_id = v.id)"


def status_category(status: str | None) -> str | None:
    """Closed category for MITOMAP's free-form status (None when absent)."""
    if status is None:
        return None
    for category, prefix in STATUS_PREFIX.items():
        if status.startswith(prefix):
            return category
    return "other"


def _gene_tokens(locus: str) -> set[str]:
    """``MT-ATP8/6`` -> {MT-ATP8, MT-ATP6}; ``MT-TS1 precursor`` -> {MT-TS1}."""
    tokens: set[str] = set()
    previous = ""
    for raw in locus.split("/"):
        token = raw.strip().split(" ")[0].upper()
        if not token.startswith("MT-") and previous:
            token = re.sub(r"[0-9A-Z]+$", token, previous, count=1)
        tokens.add(token)
        previous = token
    return tokens


class Repository:
    """One open snapshot; every query is parameterized and bounded."""

    def __init__(self, path: Path) -> None:
        """Open ``path`` read-only and index the locus vocabulary."""
        try:
            # Opened in a worker thread, queried on the event loop; read-only + immutable
            # makes sharing the connection safe.
            self._conn = sqlite3.connect(
                f"file:{path}?mode=ro&immutable=1", uri=True, check_same_thread=False
            )
            self._conn.row_factory = sqlite3.Row
            self.meta: dict[str, str] = dict(self._conn.execute("SELECT key, value FROM meta"))
            loci = [r[0] for r in self._conn.execute("SELECT DISTINCT locus FROM variant")]
        except sqlite3.Error as exc:
            raise DataUnavailableError("The MITOMAP snapshot cannot be opened.") from exc
        self._locus_index: dict[str, list[str]] = {}
        for locus in loci:
            if locus:
                for token in _gene_tokens(locus):
                    self._locus_index.setdefault(token, []).append(locus)

    @property
    def loci(self) -> list[str]:
        """Every gene/region token that search_variants(locus=) accepts."""
        return sorted(self._locus_index)

    def counts(self) -> dict[str, int]:
        """Record counts per kind, plus references."""
        out = {
            k: int(n)
            for k, n in self._conn.execute("SELECT kind, COUNT(*) FROM variant GROUP BY kind")
        }
        out["disease_mutations"] = out.get("mutation_coding_control", 0) + out.get(
            "mutation_rna", 0
        )
        out["references"] = int(self._conn.execute("SELECT COUNT(*) FROM reference").fetchone()[0])
        return out

    def check_reference(self, query: VariantQuery) -> None:
        """Reject a ref allele that contradicts a rCRS base the snapshot knows."""
        if query.ref is None:
            return
        for offset, base in enumerate(query.ref):
            row = self._conn.execute(
                "SELECT base FROM rcrs_base WHERE position = ?", (query.position + offset,)
            ).fetchone()
            if row is not None and row[0] != base:
                raise InvalidInputError(
                    "The reference allele does not match rCRS (NC_012920.1) at this position.",
                    field="variant",
                    allowed=[row[0]] if len(query.ref) == 1 else None,
                    hint="Check the reference allele; positions are rCRS, not RSRS or hg18.",
                    reason="reference_mismatch",
                )

    def _references(self, variant_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT r.pmid, r.year, r.title, r.journal FROM variant_reference vr "
            "JOIN reference r ON r.id = vr.reference_id WHERE vr.variant_id = ? "
            "ORDER BY r.year, r.id",
            (variant_id,),
        )
        return [dict(row) for row in rows]

    def find(self, query: VariantQuery) -> list[dict[str, Any]]:
        """Every MITOMAP record for this exact allele (mutation and/or polymorphism)."""
        args: tuple[object, ...]
        if query.allele is not None:
            sql, args = "SELECT * FROM variant WHERE allele = ?", (query.allele,)
        else:
            sql = "SELECT * FROM variant WHERE position = ? AND ref = ? AND alt = ?"
            args = (query.position, query.ref, query.alt)
        records = [dict(row) for row in self._conn.execute(f"{sql} ORDER BY kind, id", args)]
        for record in records:
            record["references"] = self._references(record["id"])
        return records

    def alleles_at(self, position: int) -> list[str]:
        """Distinct MITOMAP alleles (HGVS where known) recorded at one position."""
        rows = self._conn.execute(
            "SELECT DISTINCT COALESCE(hgvs, allele) FROM variant WHERE position = ? "
            "AND COALESCE(hgvs, allele) IS NOT NULL ORDER BY 1",
            (position,),
        )
        return [row[0] for row in rows]

    def search(
        self,
        *,
        locus: str | None = None,
        disease_query: str | None = None,
        status: str | None = None,
        record_type: str = "disease_mutation",
        position_start: int | None = None,
        position_end: int | None = None,
        limit: int,
        offset: int,
        with_references: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        """One page of matching records (optionally with references) and the honest total."""
        where: list[str] = []
        args: list[Any] = []
        if record_type == "disease_mutation":
            where.append("kind != 'polymorphism'")
        elif record_type == "polymorphism":
            where.append("kind = 'polymorphism'")
        if locus is not None:
            names = self._locus_index.get(locus.strip().upper())
            if names is None:
                raise InvalidInputError(
                    "Unknown MITOMAP locus.",
                    field="locus",
                    hint="Use an MT- gene/region symbol such as MT-TL1 or MT-ATP6.",
                    did_you_mean=_close(locus, self.loci),
                    reason="unknown_locus",
                )
            where.append(f"locus IN ({', '.join('?' * len(names))})")
            args += names
        terms = [t.strip() for t in (disease_query or "").split("|") if t.strip()][:5]
        if terms:
            where.append("(" + " OR ".join(["disease LIKE ? ESCAPE '\\'"] * len(terms)) + ")")
            args += [f"%{re.sub(r'([\\%_])', r'\\\1', term)}%" for term in terms]
        if status is not None:
            where.append("status LIKE ?")
            args.append(f"{STATUS_PREFIX[status]}%")
        if position_start is not None:
            where.append("position >= ?")
            args.append(position_start)
        if position_end is not None:
            where.append("position <= ?")
            args.append(position_end)
        clause = f" WHERE {' AND '.join(where)}" if where else ""
        total = self._conn.execute(f"SELECT COUNT(*) FROM variant v{clause}", args).fetchone()[0]  # noqa: S608
        rows = self._conn.execute(
            f"SELECT v.*, {_REF_COUNT} AS reference_count FROM variant v{clause} "  # noqa: S608
            "ORDER BY position, kind, id LIMIT ? OFFSET ?",
            [*args, limit, offset],
        )
        page = [dict(row) for row in rows]
        if with_references:
            for record in page:
                record["references"] = self._references(record["id"])
        return page, int(total)


def _close(value: str, vocabulary: list[str]) -> list[str]:
    return difflib.get_close_matches(value.strip().upper(), vocabulary, n=3, cutoff=0.6)
