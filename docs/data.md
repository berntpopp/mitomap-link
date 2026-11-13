# Data

## Source

MITOMAP publishes its whole database daily as a plain-text PostgreSQL dump,
`https://mitomap.org/downloads/mitomap.dump.sql.gz` (~64 MB gzip, ~470 MB SQL; pg_dump 15,
schema `mitomap`). The live MITOMAP pages and MITOMASTER sit behind a Cloudflare challenge
and are not used.

The dump is **untrusted input**. It is never restored into PostgreSQL and no statement in
it is executed: `mitomap_link/ingest/dump.py` reads only the data lines of
`COPY mitomap.<table> (...) FROM stdin;` blocks for an explicit allowlist of tables and
decodes them as PostgreSQL text-format COPY. Every other line (SQL, `\restrict`, the two
`plpgsql` helper functions) is skipped unread. A missing table, a column-count mismatch or
an unterminated block fails the build.

| Dump table | Used for |
|---|---|
| `mmutation` | Coding/control-region disease mutations |
| `rtmutation` | rRNA/tRNA disease mutations |
| `polymorphism` | Population polymorphisms (no disease, no status) |
| `variants_count` | GenBank full-length and control-region counts per allele |
| `summary` | GenBank sequence totals (the frequency denominators) |
| `*_reference`, `reference` | Literature links; `nlmid` holds the PMID |
| `locus` | Locus coordinates (derives the locus of a polymorphism) |
| `edit_date` | MITOMAP's per-table edit dates (reported, not hashed into the tag) |

Tables with submitter contact data (`unpublished`, `submitted_variant*`) are never read.

## The derived snapshot

`mitomap-link-data build` writes one SQLite file (`variant`, `reference`,
`variant_reference`, `rcrs_base`, `locus`, `meta`). Values are MITOMAP's own; `.` and empty
placeholders become NULL, nothing is inferred. The build is deterministic — rows are
sorted, the file is `VACUUM`ed, and no wall-clock value is stored — so one dump and one
toolchain always produce the same bytes. `rcrs_base` holds the rCRS base implied by
MITOMAP's single-base substitutions (positions with conflicting evidence are dropped); it
lets `get_variant` reject a reference allele that contradicts rCRS.

## Data releases

`.github/workflows/data-release.yml` (manual dispatch on `main`) downloads the dump once,
builds, and publishes four assets as an immutable, attested release:

| Asset | |
|---|---|
| `mitomap.sqlite.gz` | The snapshot, gzip with `mtime=0`. Its SHA-256 is the fleet `data.digest`. |
| `manifest.json` | Tag, digests, dump URL/SHA-256/size/Last-Modified, record counts, builder revision, licence, attribution. |
| `data-authorization.json` | The redistribution record (below). |
| `SHA256SUMS` | Checksums of the three files above. |

The tag is content-addressed, `data-mitomap-<first 16 hex of the expanded SQLite SHA-256>`,
so an unchanged snapshot is never published twice. Publication waits on the
`data-release` environment (owner approval, `main` only).

To ship a new snapshot: dispatch the workflow, approve the gate, then in a reviewed PR set
`mitomap_link/store/pin.py` and `container-release.json` `data.release_tag`/`data.digest`
to the new release (`tests/unit/test_release_contract.py` checks they agree) and cut a new
application release.

## Licence and attribution

All MITOWeb content, including MITOMAP, is licensed **CC BY 3.0**: "anyone [may] download,
reuse, reprint, modify, distribute, and/or copy content, so long as the original authors
and source are cited" ([MITOWIKI HelpTerms](https://web.archive.org/web/20260312104539/https://mitomap.org/foswiki/bin/view/MITOWIKI/HelpTerms)).
`release/data-authorization.json` records the repository owner's determination
(2026-11-13) that redistributing this derived, attributed research-use snapshot is
permitted. It is not an approval by MITOMAP or CHOP and not a legal opinion. Every data
response carries `recommended_citation`:

> MITOMAP: A Human Mitochondrial Genome Database. https://www.mitomap.org. Lott MT,
> Leipzig JN, Derbeneva O, Xie HM, Chalkia D, Sarmady M, Procaccio V, Wallace DC. mtDNA
> Variation and Analysis Using MITOMAP and MITOMASTER. *Curr Protoc Bioinformatics*.
> 2013;44:1.23.1-26. doi:10.1002/0471250953.bi0123s44.

`tests/fixtures/mitomap.dump.excerpt.sql` is a tiny excerpt of the dump (a few dozen rows,
reference abstracts blanked) under the same terms.

## Out of scope

MITOMASTER sequence analysis and haplogroup assignment, live MITOMAP pages, MITOMAP's
large-deletion/insertion/rearrangement tables, somatic variants, and any clinical
classification.
