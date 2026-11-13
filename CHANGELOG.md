# Changelog

All notable changes to mitomap-link are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- `get_variant(response_mode=full)` capped at 50 fenced reference titles per record (every
  PMID still in `pmids`); m.3243A>G full was 215 KB / 496 fenced objects, over the
  Response-Envelope v1.1 128-object ceiling.
- `search_variants` standard/full return PMIDs per row instead of per-row fenced titles
  (a 20-row page held 200 fenced objects).
- MITOMAP `disease` text and `status_note` are now fenced `untrusted_text` at every
  response_mode (Response-Envelope v1.1); read `.text`.
- `search_variants(locus=)` accepts bare mitochondrial gene symbols (`ATP6`, `ND4`, `TL1`).
- `genbank.control_region` is `count: null, status: outside_control_region` for alleles
  outside m.16024-576 (MITOMAP's 0 there meant "not covered", not "absent").
- `invalid_input` hints only point at `allowed_values` when the envelope carries them.
- Data responses carry a short `license`; the full redistribution statement stays in
  `get_server_capabilities`.

### Added

- `search_variants(sort_by="reference_count")` ranks the most-published records first.
- `disease_query` also splits alternatives on a spaced ` / ` (MITOMAP's own separator)
  and ` OR `.

## [0.1.0] - 2026-11-13

### Added

- First release. MCP server for MITOMAP mitochondrial DNA variants on rCRS
  (NC_012920.1), served from the pinned data release `data-mitomap-a6646827e6157779`:
  a deterministic SQLite subset of the MITOMAP daily dump (Last-Modified
  2026-11-11, SHA-256 `ce7bea0b…cd6d`), parsed as COPY text and never restored or
  executed. 1,100 disease mutations, 19,462 polymorphisms, 3,462 references.
- Tools: `get_variant`, `search_variants`, `get_server_capabilities`, `get_diagnostics`.
  rCRS normalization of HGVS / `MT-`/`M-`/`chrM-` ids / legacy `A3243G` / HGVS indels;
  other mitochondrial references and rCRS base mismatches rejected. MITOMAP status
  verbatim with its category and the bracketed ClinGen VCEP rating split out; plasmy
  flags verbatim; GenBank counts with denominators; missing stays null; fenced
  reference titles; gnomAD mito cross-reference in `next_commands`; CC BY 3.0
  `recommended_citation` on every data response.
- Data releases: `data-release.yml` publishes content-addressed, attested
  `data-mitomap-<sha16>` releases behind the `data-release` environment, with the
  repository owner's redistribution record; an init container materializes and
  verifies the pin and `/health` reports runtime-v1 data identity.
- Fleet standards: Tool-Naming v1.1, Response-Envelope v1/v1.1, Tool-Schema
  Documentation, Container Hardening v1 (non-root 10001, read-only rootfs, code-only
  image), vendored transport/behaviour/contract-truth conformance probes.
