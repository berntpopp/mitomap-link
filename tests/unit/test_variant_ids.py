"""Variant-id normalization onto rCRS (NC_012920.1) coordinates."""

from __future__ import annotations

import pytest

from mitomap_link.exceptions import InvalidInputError
from mitomap_link.variant_ids import VariantQuery, gnomad_variant_id, parse_variant

MELAS = VariantQuery(position=3243, ref="A", alt="G")


@pytest.mark.parametrize(
    "text",
    [
        "m.3243A>G",
        "M.3243a>g",
        "NC_012920.1:m.3243A>G",
        "NC_012920:m.3243A>G",
        "J01415.2:m.3243A>G",
        "MT-3243-A-G",
        "M-3243-A-G",
        "chrM-3243-A-G",
        "chrM:3243 A>G",
        "chrM:3243:A:G",
        "chrMT:3243A>G",
        "MT:g.3243A>G",
        "3243A>G",
        "A3243G",
        "  m.3243A>G  ",
    ],
)
def test_substitution_aliases_normalize_to_rcrs(text: str) -> None:
    assert parse_variant(text) == MELAS


def test_position_ref_alt_text_forms() -> None:
    assert parse_variant("8344 a g") == VariantQuery(8344, "A", "G")


def test_multi_nucleotide_substitution() -> None:
    assert parse_variant("m.8993TG>CA") == VariantQuery(8993, "TG", "CA")


def test_hgvs_indel_becomes_exact_allele_lookup() -> None:
    query = parse_variant("NC_012920.1:m.5133_5134del")
    assert query == VariantQuery(5133, None, None, allele="m.5133_5134del")
    assert parse_variant("m.309_310insC").allele == "m.309_310insC"


@pytest.mark.parametrize(
    "text", ["NC_001807.4:m.3243A>G", "AF347015.1:m.3243A>G", "RSRS:m.3243A>G", "hg18:3243A>G"]
)
def test_other_mitochondrial_references_are_rejected(text: str) -> None:
    with pytest.raises(InvalidInputError) as info:
        parse_variant(text)
    assert info.value.field == "variant"
    assert info.value.allowed == ["NC_012920.1", "J01415.2"]


@pytest.mark.parametrize(
    "text",
    [
        "chr1-3243-A-G",
        "c.3243A>G",
        "p.R340H",
        "m.0A>G",
        "m.16570A>G",
        "m.3243A>A",
        "x",
        "",
        "m.3243A>GG",
    ],
)
def test_malformed_or_non_mitochondrial_ids_are_rejected(text: str) -> None:
    with pytest.raises(InvalidInputError):
        parse_variant(text)


def test_gnomad_variant_id_only_for_substitutions() -> None:
    assert gnomad_variant_id(MELAS) == "M-3243-A-G"
    assert gnomad_variant_id(VariantQuery(5133, None, None, allele="m.5133_5134del")) is None
