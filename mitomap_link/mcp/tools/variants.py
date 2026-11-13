"""Variant tools: get_variant, search_variants."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from pydantic import Field

from mitomap_link.constants import (
    LICENSE,
    MAX_SEARCH_LIMIT,
    RECOMMENDED_CITATION,
    REFERENCE_SEQUENCE,
    SOURCE_NAME,
)
from mitomap_link.exceptions import InvalidInputError
from mitomap_link.mcp.annotations import READ_ONLY_OPEN_WORLD
from mitomap_link.mcp.envelope import McpErrorContext, run_mcp_tool
from mitomap_link.mcp.next_commands import after_search, after_variant
from mitomap_link.mcp.service_adapters import get_repository
from mitomap_link.mcp.shaping import ResponseModeValue, project_record
from mitomap_link.store.repository import RecordType, StatusCategory
from mitomap_link.variant_ids import MT_LENGTH, gnomad_variant_id, hgvs, parse_variant

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from mitomap_link.store.repository import Repository

ResponseMode = Annotated[
    ResponseModeValue,
    Field(
        description="Verbosity: minimal (ids, locus, disease, status) | compact (default; + "
        "alleles, plasmy, GenBank counts, reference_count) | standard (+ up to 10 references "
        "with fenced titles) | full (+ every reference and every PMID)."
    ),
]
Position = Annotated[
    int | None,
    Field(ge=1, le=MT_LENGTH, description="rCRS position (1-16569), inclusive.", examples=[3243]),
]

ABSENCE_NOTE = (
    "MITOMAP lists no disease mutation or polymorphism for this exact allele in this snapshot. "
    "That is not evidence of benignity or pathogenicity; check gnomAD (next_commands) and the "
    "other alleles MITOMAP records at this position."
)


def _provenance(payload: dict[str, Any], repo: Repository) -> dict[str, Any]:
    payload["recommended_citation"] = RECOMMENDED_CITATION
    payload["license"] = LICENSE
    payload["_meta"] = {
        **payload.get("_meta", {}),
        "source": SOURCE_NAME,
        "data_version": f"mitomap-dump@{repo.meta.get('source_last_modified', 'unknown')}",
    }
    return payload


def register_variant_tools(mcp: FastMCP) -> None:
    """Register the MITOMAP variant tools on a FastMCP instance."""

    @mcp.tool(
        name="get_variant",
        title="Get MITOMAP Variant",
        annotations=READ_ONLY_OPEN_WORLD,
        output_schema=None,
        tags={"variant", "mitochondrial"},
        description=(
            "Look up one mtDNA allele in MITOMAP on the rCRS reference (NC_012920.1): every "
            "MITOMAP record for it (coding/control-region or rRNA/tRNA disease mutation, "
            "polymorphism) with locus, disease, MITOMAP status verbatim ('Reported', 'Cfrm' = "
            "confirmed; a bracketed ClinGen VCEP rating is split out), homoplasmy/heteroplasmy "
            "as reported, GenBank count/frequency and PMIDs. Accepts m.3243A>G, "
            "NC_012920.1:m.3243A>G, MT-3243-A-G, chrM:3243 A>G, A3243G, and HGVS indels "
            "(m.5133_5134del, exact MITOMAP allele match). Other mito references (Yoruba "
            "NC_001807, RSRS) and rCRS reference-base mismatches are rejected. An allele "
            "MITOMAP does not list returns found=false, not an error. "
            "Signature: get_variant(variant, response_mode=)."
        ),
    )
    async def get_variant(
        variant: Annotated[
            str,
            Field(
                min_length=1,
                max_length=80,
                description="mtDNA variant on rCRS, e.g. m.3243A>G, MT-3243-A-G, "
                "chrM:8344 A>G or m.5133_5134del.",
                examples=["m.3243A>G", "MT-8344-A-G", "m.11778G>A"],
            ),
        ],
        response_mode: ResponseMode = "compact",
    ) -> dict[str, Any]:
        async def call() -> dict[str, Any]:
            query = parse_variant(variant)
            repo = await get_repository()
            repo.check_reference(query)
            records = repo.find(query)
            found = bool(records)
            gnomad_id = gnomad_variant_id(query)
            payload: dict[str, Any] = {
                "query": {
                    "hgvs": hgvs(query),
                    "reference_sequence": REFERENCE_SEQUENCE,
                    "position": query.position,
                    "ref": query.ref,
                    "alt": query.alt,
                    "gnomad_variant_id": gnomad_id,
                },
                "found": found,
                "records": [project_record(r, response_mode, repo.meta) for r in records],
            }
            if not found:
                payload["absence_note"] = ABSENCE_NOTE
                payload["other_alleles_at_position"] = repo.alleles_at(query.position)
            loci = sorted({r["locus"] for r in records if r.get("locus")})
            payload["_meta"] = {
                "next_commands": after_variant(gnomad_id, loci, query.position, found)
            }
            return _provenance(payload, repo)

        return await run_mcp_tool("get_variant", call, context=McpErrorContext("get_variant"))

    @mcp.tool(
        name="search_variants",
        title="Search MITOMAP Variants",
        annotations=READ_ONLY_OPEN_WORLD,
        output_schema=None,
        tags={"variant", "mitochondrial", "search"},
        description=(
            "Search MITOMAP mtDNA variants by locus (MT-TL1, MT-ATP6, MT-CR...), disease text, "
            "MITOMAP status category and/or an rCRS position range. record_type defaults to "
            "disease_mutation (MITOMAP's coding/control and rRNA/tRNA mutation lists); use "
            "polymorphism or any for population polymorphisms. Unknown loci are rejected. "
            "Ordered by position; returns results with total/truncated/next_offset. "
            "Signature: search_variants(locus=, disease_query=, status=, record_type=, "
            "position_start=, position_end=, limit=, offset=, response_mode=)."
        ),
    )
    async def search_variants(
        locus: Annotated[
            str | None,
            Field(
                max_length=40,
                description="MITOMAP locus / MT- gene symbol (case-insensitive).",
                examples=["MT-ATP6", "MT-TL1"],
            ),
        ] = None,
        disease_query: Annotated[
            str | None,
            Field(
                max_length=100,
                description="Case-insensitive substring of MITOMAP's disease text, e.g. "
                "'Leigh', 'LHON', 'MELAS'; separate up to 5 alternatives with '|' "
                "(Leigh|NARP|MILS).",
                examples=["Leigh"],
            ),
        ] = None,
        status: Annotated[
            StatusCategory | None,
            Field(
                description="MITOMAP status category: reported, confirmed (Cfrm), "
                "conflicting_reports, unclear."
            ),
        ] = None,
        record_type: Annotated[
            RecordType,
            Field(description="disease_mutation (default), polymorphism, or any."),
        ] = "disease_mutation",
        position_start: Position = None,
        position_end: Position = None,
        limit: Annotated[
            int, Field(ge=1, le=MAX_SEARCH_LIMIT, description="Page size (1-100, default 20).")
        ] = 20,
        offset: Annotated[int, Field(ge=0, description="Rows to skip (default 0).")] = 0,
        response_mode: ResponseMode = "compact",
    ) -> dict[str, Any]:
        async def call() -> dict[str, Any]:
            if position_start and position_end and position_start > position_end:
                raise InvalidInputError(
                    "position_start must not exceed position_end.",
                    field="position_start",
                    hint="Swap the bounds.",
                    reason="inverted_range",
                )
            repo = await get_repository()
            rows, total = repo.search(
                locus=locus,
                disease_query=disease_query,
                status=status,
                record_type=record_type,
                position_start=position_start,
                position_end=position_end,
                limit=limit,
                offset=offset,
                with_references=response_mode in ("standard", "full"),
            )
            page = [project_record(r, response_mode, repo.meta) for r in rows]
            more = offset + len(page) < total
            return _provenance(
                {
                    "results": page,
                    "total": total,
                    "returned": len(page),
                    "offset": offset,
                    "truncated": more,
                    "next_offset": offset + len(page) if more else None,
                    "_meta": {
                        "pagination": {"total_count": total, "has_more": more},
                        "next_commands": after_search(page),
                    },
                },
                repo,
            )

        return await run_mcp_tool(
            "search_variants", call, context=McpErrorContext("search_variants")
        )
