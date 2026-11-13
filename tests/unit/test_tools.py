"""End-to-end tool behaviour through the FastMCP facade, against the fixture snapshot."""

from __future__ import annotations

from typing import Any

EXPECTED_TOOLS = {"get_server_capabilities", "get_diagnostics", "get_variant", "search_variants"}


async def _call(facade: Any, structured: Any, name: str, args: dict[str, Any]) -> dict[str, Any]:
    return structured(await facade.call_tool(name, args))


async def test_tool_inventory(facade: Any) -> None:
    assert {t.name for t in await facade.list_tools()} == EXPECTED_TOOLS


async def test_get_variant_melas(facade: Any, structured: Any) -> None:
    env = await _call(facade, structured, "get_variant", {"variant": "MT-3243-A-G"})
    assert env["success"] is True and env["found"] is True
    assert env["query"]["hgvs"] == "m.3243A>G"
    assert env["query"]["reference_sequence"] == "NC_012920.1"
    mutation = next(r for r in env["records"] if r["record_type"] == "mutation_rna")
    assert mutation["locus"] == "MT-TL1"
    assert mutation["mitomap_status"] == "Cfrm [P]"
    assert mutation["mitomap_status_category"] == "confirmed"
    assert mutation["clingen_classification_in_status"] == "P"
    assert mutation["plasmy_reported"] == {"homoplasmy": "-", "heteroplasmy": "+"}
    gb = mutation["genbank"]["full_length"]
    assert gb["count"] == 10 and gb["total_sequences"] == 66775
    assert mutation["reference_count"] > 0 and "pmids" not in mutation
    assert "MITOMAP" in env["recommended_citation"]
    assert "CC BY 3.0" in env["license"]
    assert env["_meta"]["unsafe_for_clinical_use"] is True
    tools = [c["tool"] for c in env["_meta"]["next_commands"]]
    assert "gnomad_get_mitochondrial_variant" in tools


async def test_polymorphism_disease_stays_missing(facade: Any, structured: Any) -> None:
    env = await _call(facade, structured, "get_variant", {"variant": "m.73A>G"})
    [record] = env["records"]
    assert record["record_type"] == "polymorphism"
    assert record["disease"] is None and record["mitomap_status"] is None


async def test_absent_variant_is_honest_empty(facade: Any, structured: Any) -> None:
    env = await _call(facade, structured, "get_variant", {"variant": "m.16000A>G"})
    assert env["success"] is True and env["found"] is False and env["records"] == []
    assert "not evidence" in env["absence_note"]


async def test_wrong_reference_is_invalid_input(facade: Any, structured: Any) -> None:
    for bad in ("NC_001807.4:m.3243A>G", "m.3243G>A"):
        env = await _call(facade, structured, "get_variant", {"variant": bad})
        assert env["success"] is False and env["error_code"] == "invalid_input"
        assert env["field"] == "variant"


async def test_references_fenced_at_standard(facade: Any, structured: Any) -> None:
    env = await _call(
        facade, structured, "get_variant", {"variant": "m.11778G>A", "response_mode": "standard"}
    )
    ref = next(r for r in env["records"] if r["references"])["references"][0]
    assert ref["title"]["kind"] == "untrusted_text"


async def test_search_by_locus_pages_honestly(facade: Any, structured: Any) -> None:
    env = await _call(facade, structured, "search_variants", {"locus": "MT-ATP6", "limit": 1})
    assert env["total"] >= 2 and env["returned"] == 1 and env["truncated"] is True
    assert env["next_offset"] == 1
    assert env["_meta"]["pagination"] == {"total_count": env["total"], "has_more": True}


async def test_search_unknown_locus_rejected(facade: Any, structured: Any) -> None:
    env = await _call(facade, structured, "search_variants", {"locus": "MT-NOPE"})
    assert env["error_code"] == "invalid_input" and env["field"] == "locus"


async def test_search_disease_and_status(facade: Any, structured: Any) -> None:
    env = await _call(
        facade, structured, "search_variants", {"disease_query": "MERRF", "status": "confirmed"}
    )
    assert [r["hgvs"] for r in env["results"]] == ["m.8344A>G"]


async def test_search_position_range_bounds_checked(facade: Any, structured: Any) -> None:
    env = await _call(
        facade, structured, "search_variants", {"position_start": 500, "position_end": 100}
    )
    assert env["error_code"] == "invalid_input"


async def test_diagnostics_reports_snapshot(facade: Any, structured: Any) -> None:
    env = await _call(facade, structured, "get_diagnostics", {})
    assert env["data_available"] is True
    assert env["record_counts"]["disease_mutations"] > 0
    assert env["source"]["last_modified"] == "fixture"


async def test_search_full_adds_references_over_compact(facade: Any, structured: Any) -> None:
    args = {"locus": "MT-ND4"}
    compact = await _call(facade, structured, "search_variants", args)
    full = await _call(facade, structured, "search_variants", {**args, "response_mode": "full"})
    assert "references" not in compact["results"][0]
    # Search rows carry PMIDs, never per-row fenced titles (object/byte ceilings).
    assert "references" not in full["results"][0] and full["results"][0]["pmids"]
    standard = await _call(
        facade, structured, "search_variants", {**args, "response_mode": "standard"}
    )
    assert "references" not in standard["results"][0]
    assert len(standard["results"][0]["pmids"]) <= 10


async def test_invalid_input_messages_name_the_reason(facade: Any, structured: Any) -> None:
    cases = {
        "NC_001807.4:m.3243A>G": "Only the rCRS",
        "m.3243G>A": "reference base does not match rCRS",
        "p.R340H": "Unrecognized mtDNA variant notation",
        "m.17000A>G": "1-16569",
    }
    for variant, expected in cases.items():
        env = await _call(facade, structured, "get_variant", {"variant": variant})
        assert expected in env["message"], (variant, env["message"])
    env = await _call(facade, structured, "search_variants", {"locus": "MT-NOPE"})
    assert "Unknown MITOMAP locus" in env["message"]


async def test_non_date_status_note_is_not_called_a_date(facade: Any, structured: Any) -> None:
    from mitomap_link.mcp.shaping import project_record

    base = {"id": "x", "kind": "mutation_coding_control", "position": 1, "status": "Reported"}
    dated = project_record({**base, "status_date": "2022.04.13"}, "compact", {})
    noted = project_record({**base, "status_date": "Reported by paper as VUS"}, "compact", {})
    assert dated["status_date"] == "2022.04.13" and dated["status_note"] is None
    assert noted["status_date"] is None
    assert noted["status_note"]["kind"] == "untrusted_text"
    assert noted["status_note"]["text"] == "Reported by paper as VUS"


async def test_standard_mode_keeps_pmids_for_full(facade: Any, structured: Any) -> None:
    args = {"variant": "m.11778G>A"}
    standard = await _call(facade, structured, "get_variant", {**args, "response_mode": "standard"})
    full = await _call(facade, structured, "get_variant", {**args, "response_mode": "full"})
    assert all("pmids" not in r for r in standard["records"])
    assert any(r.get("pmids") for r in full["records"])


async def test_disease_query_accepts_alternatives(facade: Any, structured: Any) -> None:
    env = await _call(facade, structured, "search_variants", {"disease_query": "MERRF|LHON"})
    diseases = " ".join(r["disease"]["text"] for r in env["results"])
    assert "MERRF" in diseases and "LHON" in diseases


async def test_dbsnp_id_gets_its_own_reason(facade: Any, structured: Any) -> None:
    env = await _call(facade, structured, "get_variant", {"variant": "rs199474657"})
    assert "dbSNP" in env["message"]


async def test_disease_text_is_fenced_at_every_mode(facade: Any, structured: Any) -> None:
    for mode in ("minimal", "compact"):
        env = await _call(
            facade, structured, "get_variant", {"variant": "m.3243A>G", "response_mode": mode}
        )
        disease = env["records"][0]["disease"]
        assert disease["kind"] == "untrusted_text" and "MELAS" in disease["text"]
        assert disease["provenance"]["record_id"] == env["records"][0]["mitomap_record_id"]


def test_full_mode_caps_fenced_reference_objects() -> None:
    from mitomap_link.mcp.shaping import FULL_REFERENCE_LIMIT, project_record

    refs = [{"pmid": str(i), "year": 2000, "title": f"t{i}", "journal": "j"} for i in range(60)]
    rec = {"id": "x", "kind": "mutation_rna", "position": 1, "references": refs}
    out = project_record(rec, "full", {})
    assert len(out["references"]) == FULL_REFERENCE_LIMIT < 60
    assert out["references_truncated"] is True and len(out["pmids"]) == 60
    assert out["reference_count"] == 60


async def test_bare_mito_gene_symbol_is_accepted(facade: Any, structured: Any) -> None:
    bare = await _call(facade, structured, "search_variants", {"locus": "atp6"})
    full = await _call(facade, structured, "search_variants", {"locus": "MT-ATP6"})
    assert bare["success"] is True and bare["total"] == full["total"] > 0


async def test_search_sorts_by_reference_count(facade: Any, structured: Any) -> None:
    env = await _call(
        facade, structured, "search_variants", {"locus": "MT-ATP6", "sort_by": "reference_count"}
    )
    counts = [r["reference_count"] for r in env["results"]]
    assert counts == sorted(counts, reverse=True) and counts[0] > counts[-1]


async def test_disease_query_accepts_spaced_slash_and_or(facade: Any, structured: Any) -> None:
    piped = await _call(facade, structured, "search_variants", {"disease_query": "MERRF|LHON"})
    for query in ("MERRF / LHON", "MERRF OR LHON"):
        env = await _call(facade, structured, "search_variants", {"disease_query": query})
        assert env["total"] == piped["total"] > 0, query


async def test_control_region_count_is_not_applicable_outside_it(
    facade: Any, structured: Any
) -> None:
    env = await _call(facade, structured, "get_variant", {"variant": "m.3243A>G"})
    cr = env["records"][0]["genbank"]["control_region"]
    assert cr["count"] is None and cr["status"] == "outside_control_region"
    assert "frequency" not in cr
    env = await _call(facade, structured, "get_variant", {"variant": "m.73A>G"})
    assert env["records"][0]["genbank"]["control_region"]["count"] > 0


async def test_hint_only_points_at_allowed_values_when_present(
    facade: Any, structured: Any
) -> None:
    env = await _call(facade, structured, "get_variant", {"variant": "m.17000A>G"})
    assert "allowed_values" not in env and "allowed_values" not in env["hint"]
    env = await _call(facade, structured, "get_variant", {"variant": "m.3243C>G"})
    assert env["allowed_values"] == ["A"] and "allowed_values" in env["hint"]
