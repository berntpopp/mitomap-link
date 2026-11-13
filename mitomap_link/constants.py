"""Static provenance: citation, license, attribution, and the research-use notice."""

from __future__ import annotations

SOURCE_NAME = "mitomap"
REFERENCE_SEQUENCE = "NC_012920.1"

RECOMMENDED_CITATION = (
    "MITOMAP: A Human Mitochondrial Genome Database. https://www.mitomap.org (CC BY 3.0). "
    "Lott MT, Leipzig JN, Derbeneva O, Xie HM, Chalkia D, Sarmady M, Procaccio V, Wallace DC. "
    "mtDNA Variation and Analysis Using MITOMAP and MITOMASTER. Curr Protoc Bioinformatics. "
    "2013;44:1.23.1-26. doi:10.1002/0471250953.bi0123s44"
)

# Stamped on every data response, so kept short; the full statement is LICENSE_STATEMENT.
LICENSE = "CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/); cite recommended_citation."
LICENSE_STATEMENT = (
    "MITOMAP content is licensed CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/): "
    "reuse and redistribution are permitted so long as the original authors and source are "
    "cited. mitomap-link serves a derived snapshot of the MITOMAP daily dump, unmodified apart "
    "from reshaping; redistribution is the repository owner's determination, not a MITOMAP "
    "approval."
)

RESEARCH_USE_NOTICE = (
    "Research use only; not for clinical decision support, diagnosis, "
    "treatment, or patient management."
)

STATUS_SEMANTICS = (
    "mitomap_status is MITOMAP's own status, verbatim: 'Reported' = one or more publications "
    "considered the variant possibly pathologic; 'Cfrm' (confirmed) = two or more independent "
    "laboratories published its pathogenicity. Neither is an assignment of pathogenicity by "
    "MITOMAP. A bracketed rating (e.g. 'Cfrm [LP]') is the ClinGen mtDNA VCEP classification "
    "MITOMAP displays; it is surfaced separately as clingen_classification_in_status and is "
    "not a ClinVar record."
)

PLASMY_SEMANTICS = (
    "plasmy_reported holds MITOMAP's homoplasmy/heteroplasmy report flags verbatim ('+' = "
    "reported in the literature; '-', 'nr' and other values exactly as MITOMAP states them). "
    "They describe published reports, not a sample, and are never inferred."
)

GENBANK_SEMANTICS = (
    "genbank.full_length / control_region: MITOMAP's count of GenBank sequences carrying the "
    "exact allele, over its sequence totals; frequency = count / total_sequences. GenBank "
    "sequences are not hand-curated and include patients. count is null (status "
    "not_tabulated) when MITOMAP lists no count for that allele representation, and "
    "control_region count is null (status outside_control_region) for alleles outside "
    "m.16024-576, which control-region sequences do not cover."
)

MAX_SEARCH_LIMIT = 100
