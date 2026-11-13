# mitomap-link design (v0.1.0)

> Historical record — the design decided for the first release (genefoundry-router#189,
> owner decision 2026-11-13). Current behaviour is documented in README.md and docs/.

## Decision

- Separate backend `mitomap-link` (namespace `mitomap`). MITOMASTER sequence analysis and
  live MITOMAP HTML are out of scope (Cloudflare challenge blocks servers; terms of
  automated use unverified).
- Source: the MITOMAP daily PostgreSQL dump `mitomap.dump.sql.gz`, CC BY 3.0 (MITOWIKI
  HelpTerms). Not GeneBe's mirror, which adds its own restrictions.
- The dump is untrusted: parsed as COPY text for an allowlist of tables, never restored
  into PostgreSQL or executed. Submitter contact tables are never read.
- Data mode: `external-reference`, data-bound, runtime-v1 identity. A content-addressed
  GitHub data release (`data-mitomap-<sha16>`, attested, published behind the
  `data-release` environment) holds a deterministic SQLite subset; an init container
  verifies it into a named volume; `/health` reports expected vs observed identity.
- Redistribution: the repository owner's determination, recorded in
  `release/data-authorization.json` with the exact attribution.

## Surface

- `get_variant(variant)`: rCRS normalization of HGVS, `MT-`/`M-`/`chrM-` dashed ids,
  `chrM:pos ref>alt`, legacy `A3243G`; other references and rCRS base mismatches rejected;
  HGVS indels by exact MITOMAP allele. Absent alleles are an honest `found: false`.
- `search_variants`: locus (validated vocabulary), disease substring, status category
  enum, record type, position window; bounded paging with honest totals.
- `get_server_capabilities`, `get_diagnostics`.
- MITOMAP status kept verbatim, with the closed category and the bracketed ClinGen VCEP
  rating split out separately. Plasmy flags verbatim. GenBank counts with denominators.
  Missing stays null. gnomAD mito is the population cross-reference in `next_commands`.
