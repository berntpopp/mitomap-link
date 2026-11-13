"""Project snapshot records into response_mode tiers, fencing upstream prose."""

from __future__ import annotations

import re
from typing import Any, Literal

from mitomap_link.constants import SOURCE_NAME
from mitomap_link.mcp.untrusted_content import fence_untrusted_text
from mitomap_link.store.repository import status_category

ResponseModeValue = Literal["minimal", "compact", "standard", "full"]
RESPONSE_MODES: tuple[str, ...] = ("minimal", "compact", "standard", "full")
DEFAULT_RESPONSE_MODE = "compact"
STANDARD_REFERENCE_LIMIT = 10
_BRACKET = re.compile(r"\[([^\]]{1,40})\]")
_DATE = re.compile(r"^\d{4}\.\d{2}\.\d{2}$")


def _genbank(count: int | None, total: str | None) -> dict[str, Any]:
    denominator = int(total) if total and total.isdigit() else None
    if count is None:
        return {"count": None, "total_sequences": denominator, "status": "not_tabulated"}
    frequency = round(count / denominator, 6) if denominator else None
    return {"count": count, "total_sequences": denominator, "frequency": frequency}


def _reference(ref: dict[str, Any], record_id: str) -> dict[str, Any]:
    title = ref.get("title")
    return {
        "pmid": ref.get("pmid"),
        "year": ref.get("year"),
        "journal": ref.get("journal"),
        "title": None
        if title is None
        else fence_untrusted_text(title, source=SOURCE_NAME, record_id=record_id).model_dump(
            mode="json"
        ),
    }


def project_record(record: dict[str, Any], mode: str, meta: dict[str, str]) -> dict[str, Any]:
    """One MITOMAP record (variant or search row) at a response_mode."""
    status = record.get("status")
    out: dict[str, Any] = {
        "mitomap_record_id": record["id"],
        "record_type": record["kind"],
        "hgvs": record.get("hgvs"),
        "locus": record.get("locus"),
        "disease": record.get("disease"),
        "mitomap_status": status,
    }
    if mode == "minimal":
        return out
    bracket = _BRACKET.search(status) if status else None
    # MITOMAP's confirmation-date column sometimes holds a curation note instead.
    status_date = record.get("status_date")
    is_date = status_date is not None and _DATE.match(status_date) is not None
    references = record.get("references")
    out.update(
        position=record["position"],
        ref=record.get("ref"),
        alt=record.get("alt"),
        mitomap_allele=record.get("allele"),
        locus_source=record.get("locus_source"),
        amino_acid_change=record.get("aa_change"),
        rna=record.get("rna"),
        mitomap_status_category=status_category(status),
        clingen_classification_in_status=bracket.group(1).strip() if bracket else None,
        status_date=status_date if is_date else None,
        status_note=None if is_date else status_date,
        plasmy_reported={
            "homoplasmy": record.get("homoplasmy"),
            "heteroplasmy": record.get("heteroplasmy"),
        },
        genbank={
            "full_length": _genbank(
                record.get("gb_fl_count"), meta.get("genbank_full_length_total")
            ),
            "control_region": _genbank(
                record.get("gb_cr_count"), meta.get("genbank_control_region_total")
            ),
        },
    )
    if references is None:
        out["reference_count"] = record.get("reference_count")
        return out
    out["reference_count"] = len(references)
    if mode == "full":
        out["pmids"] = [r["pmid"] for r in references if r.get("pmid")]
    if mode in ("standard", "full"):
        shown = references if mode == "full" else references[:STANDARD_REFERENCE_LIMIT]
        out["references"] = [
            _reference(ref, f"{record['id']}#reference{i}") for i, ref in enumerate(shown)
        ]
        out["references_truncated"] = len(shown) < len(references)
    return out
