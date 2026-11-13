"""Normalize caller variant ids onto rCRS (NC_012920.1) ``m.`` coordinates.

Accepted: HGVS ``m.3243A>G`` (optionally ``NC_012920.1:``/``J01415.2:`` qualified),
chromosome-alias forms ``chrM:3243 A>G`` / ``MT-3243-A-G`` / ``M:g.3243A>G``, bare
``3243A>G``, MITOMAP's legacy ``A3243G``, and HGVS indels (``m.5133_5134del``), which are
looked up by their exact MITOMAP allele string. Any other reference sequence (Yoruba
NC_001807 / AF347015, RSRS, hg18 chrM, ...) is rejected rather than silently remapped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from mitomap_link.exceptions import InvalidInputError

MT_LENGTH = 16569
RCRS_ACCESSIONS = ["NC_012920.1", "J01415.2"]
_RCRS_PREFIXES = {"nc_012920", "nc_012920.1", "j01415", "j01415.2"}
_CHROM_ALIASES = {"chrm", "chrmt", "mt", "m"}

_PREFIXED = re.compile(r"^([A-Za-z][A-Za-z0-9_]*(?:\.\d+)?):(.+)$")
_DASHED = re.compile(r"^(?:chrM|chrMT|MT|M)-(\d+)-([ACGT]+)-([ACGT]+)$", re.IGNORECASE)
_SUBST = re.compile(r"^(\d+)\s*([ACGT]+)\s*>\s*([ACGT]+)$", re.IGNORECASE)
_SPACED = re.compile(r"^(\d+)[\s:]+([ACGT]+)[\s:]+([ACGT]+)$", re.IGNORECASE)
_LEGACY = re.compile(r"^([ACGT])(\d+)([ACGT])$", re.IGNORECASE)
_INDEL = re.compile(r"^(\d+)(_\d+)?(delins|del|ins|dup|inv)([ACGT]*)$", re.IGNORECASE)


@dataclass(frozen=True)
class VariantQuery:
    """A normalized rCRS variant: a substitution, or an exact MITOMAP indel allele."""

    position: int
    ref: str | None
    alt: str | None
    allele: str | None = None


def _invalid(message: str, reason: str, *, allowed: list[str] | None = None) -> InvalidInputError:
    return InvalidInputError(
        message,
        field="variant",
        allowed=allowed,
        reason=reason,
        hint="Use rCRS HGVS such as m.3243A>G (or NC_012920.1:m.3243A>G, MT-3243-A-G).",
    )


def _substitution(position: str, ref: str, alt: str) -> VariantQuery:
    pos, ref, alt = int(position), ref.upper(), alt.upper()
    if not 1 <= pos <= MT_LENGTH:
        raise _invalid(f"rCRS position must be 1-{MT_LENGTH}.", "position_out_of_range")
    if ref == alt or len(ref) != len(alt):
        raise _invalid(
            "ref and alt must differ and have equal length (use HGVS for indels).",
            "invalid_substitution",
        )
    return VariantQuery(pos, ref, alt)


def _body(text: str, *, qualified: bool) -> VariantQuery:
    lowered = text.lower()
    if lowered.startswith("m.") or (qualified and lowered.startswith("g.")):
        text = text[2:]
    for pattern in (_SUBST, _SPACED):
        if match := pattern.match(text):
            return _substitution(*match.groups())
    if match := _LEGACY.match(text):
        return _substitution(match.group(2), match.group(1), match.group(3))
    if match := _INDEL.match(text):
        start, end, kind, bases = match.groups()
        if not 1 <= int(start) <= MT_LENGTH:
            raise _invalid(f"rCRS position must be 1-{MT_LENGTH}.", "position_out_of_range")
        allele = f"m.{start}{end or ''}{kind.lower()}{bases.upper()}"
        return VariantQuery(int(start), None, None, allele=allele)
    raise _invalid("Unrecognized mitochondrial variant notation.", "unrecognized_notation")


def parse_variant(variant: str) -> VariantQuery:
    """Parse caller variant text onto rCRS coordinates (raises InvalidInputError)."""
    text = variant.strip()
    if re.fullmatch(r"rs\d+", text, re.IGNORECASE):
        raise _invalid("dbSNP ids are not MITOMAP identifiers.", "dbsnp_id")
    if match := _DASHED.match(text):
        return _substitution(*match.groups())
    if match := _PREFIXED.match(text):
        label, rest = match.group(1).lower(), match.group(2).strip()
        if label in _CHROM_ALIASES or label in _RCRS_PREFIXES:
            return _body(rest, qualified=True)
        raise _invalid(
            "Only the rCRS reference is supported.",
            "unsupported_reference",
            allowed=RCRS_ACCESSIONS,
        )
    return _body(text, qualified=False)


def hgvs(query: VariantQuery) -> str:
    """The rCRS HGVS string for a normalized query."""
    return query.allele or f"m.{query.position}{query.ref}>{query.alt}"


def gnomad_variant_id(query: VariantQuery) -> str | None:
    """gnomAD's mitochondrial id (``M-3243-A-G``) for a single-base substitution."""
    if query.allele is None and query.ref and query.alt and len(query.ref) == 1:
        return f"M-{query.position}-{query.ref}-{query.alt}"
    return None
