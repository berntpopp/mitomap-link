"""SQLite repository queries over the fixture-built snapshot."""

from __future__ import annotations

import pytest

from mitomap_link.exceptions import InvalidInputError
from mitomap_link.store.repository import Repository
from mitomap_link.variant_ids import parse_variant


def test_get_returns_every_matching_record_with_references(repo: Repository) -> None:
    records = repo.find(parse_variant("m.11778G>A"))
    kinds = {r["kind"] for r in records}
    assert "mutation_coding_control" in kinds
    mutation = next(r for r in records if r["kind"] == "mutation_coding_control")
    assert mutation["status"] == "Cfrm [P]"
    assert mutation["references"]


def test_indel_matches_exact_mitomap_allele(repo: Repository) -> None:
    [record] = repo.find(parse_variant("m.5133_5134del"))
    assert record["allele"] == "m.5133_5134del"


def test_absent_variant_is_empty(repo: Repository) -> None:
    assert repo.find(parse_variant("m.16000A>G")) == []


def test_reference_allele_mismatch_is_rejected(repo: Repository) -> None:
    with pytest.raises(InvalidInputError) as info:
        repo.check_reference(parse_variant("m.3243G>A"))
    assert info.value.allowed == ["A"]
    repo.check_reference(parse_variant("m.3243A>G"))  # matching: no error
    repo.check_reference(parse_variant("m.1A>G"))  # unknown position: cannot check, no error


def test_alleles_at_position(repo: Repository) -> None:
    assert "m.3243A>G" in repo.alleles_at(3243)


def test_search_by_locus_is_paged_with_honest_total(repo: Repository) -> None:
    rows, total = repo.search(locus="MT-ATP6", limit=1, offset=0)
    assert total >= 2 and len(rows) == 1
    rows2, total2 = repo.search(locus="mt-atp6", limit=5, offset=0)
    assert total2 == total and len(rows2) == total


def test_search_unknown_locus_is_rejected(repo: Repository) -> None:
    with pytest.raises(InvalidInputError) as info:
        repo.search(locus="MT-NOPE", limit=5, offset=0)
    assert info.value.field == "locus"


def test_search_by_disease_text_and_status(repo: Repository) -> None:
    rows, total = repo.search(disease_query="leigh", status="confirmed", limit=50, offset=0)
    assert total == len(rows) > 0
    assert all("leigh" in r["disease"].lower() and r["status"].startswith("Cfrm") for r in rows)


def test_search_polymorphisms_by_position_range(repo: Repository) -> None:
    rows, total = repo.search(
        record_type="polymorphism", position_start=60, position_end=300, limit=50, offset=0
    )
    assert total == len(rows) > 0
    assert all(r["kind"] == "polymorphism" and 60 <= r["position"] <= 300 for r in rows)


def test_meta(repo: Repository) -> None:
    assert repo.meta["genbank_full_length_total"] == "66775"


async def test_repository_opened_in_worker_thread_is_usable(fixture_database: object) -> None:
    """get_repository opens via asyncio.to_thread; tools then query on the loop thread."""
    import asyncio
    from pathlib import Path

    repo = await asyncio.to_thread(Repository, Path(str(fixture_database)))
    assert repo.find(parse_variant("m.3243A>G"))


def test_disease_query_wildcards_are_literal(repo: Repository) -> None:
    assert repo.search(disease_query="%", limit=5, offset=0)[1] == 0
    assert repo.search(disease_query="_|%", limit=5, offset=0)[1] == 0
