# mitomap-link

[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://github.com/berntpopp/mitomap-link/actions/workflows/ci.yml/badge.svg)](https://github.com/berntpopp/mitomap-link/actions/workflows/ci.yml)
[![Conformance](https://github.com/berntpopp/mitomap-link/actions/workflows/conformance.yml/badge.svg)](https://github.com/berntpopp/mitomap-link/actions/workflows/conformance.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

An MCP (Model Context Protocol) server for [MITOMAP](https://www.mitomap.org), the human
mitochondrial genome database: mtDNA disease mutations and polymorphisms on the rCRS
reference with MITOMAP status, plasmy reports, GenBank frequency and literature, served
from a digest-pinned snapshot of the MITOMAP daily dump over Streamable HTTP or stdio.

> [!IMPORTANT]
> Research use only. Not clinical decision support. Do not use for diagnosis,
> treatment, triage, or patient management.

## Why

Mitochondrial variants are easy to get wrong: positions are relative to the rCRS
(NC_012920.1), not the Yoruba sequence older pipelines used; MITOMAP writes RNA mutations
in a legacy `A3243G` style; its "Cfrm" status reports published literature rather than a
pathogenicity call; and its plasmy flags describe reports, not a sample.

`mitomap-link` hands an agent the MITOMAP record without paraphrase. It normalizes
`m.3243A>G`, `MT-3243-A-G`, `chrM:3243 A>G` and `A3243G` onto rCRS and rejects other
references and reference-base mismatches outright. It keeps the MITOMAP status verbatim
and splits out the bracketed ClinGen VCEP rating separately. GenBank counts come with
their denominators, and a missing value stays `null`. Population frequency and
heteroplasmy distributions belong to gnomAD, which `next_commands` points to; the tools
do not run MITOMASTER sequence analysis or assign haplogroups.

## Quick start

Hosted — no install, through the GeneFoundry router (namespace `mitomap`, once deployed):

```bash
claude mcp add --transport http genefoundry https://genefoundry.org/mcp
```

Local (Python 3.14+, [uv](https://github.com/astral-sh/uv)). Production verifies a pinned
data release that an init container materializes; for development, build a snapshot from
the test fixture and serve it directly:

```bash
make install          # uv sync --group dev
make dev-data         # build data/dev.sqlite from tests/fixtures (tiny excerpt)
MITOMAP_LINK_DATA__LOCAL_DATABASE=data/dev.sqlite make dev   # http://127.0.0.1:8000/mcp
```

```bash
claude mcp add --transport http mitomap-link --scope user http://127.0.0.1:8000/mcp
```

The full dataset runs in Docker (`make docker-up`), which fetches and verifies the pinned
release. Serving over HTTP behind a proxy requires adding the public hostname to the exact
Host allowlist — read [Configuration](docs/configuration.md) first.

## Tools

| Tool | Purpose |
|------|---------|
| `get_variant` | **Start here.** Every MITOMAP record for one rCRS allele: disease, status, plasmy, GenBank frequency, PMIDs. |
| `search_variants` | Browse by locus (MT-TL1, MT-ATP6), disease text, MITOMAP status category or position window. |
| `get_server_capabilities` | Discovery surface: tools, signatures, accepted notations, semantics, license, data pin. |
| `get_diagnostics` | Whether the pinned data release is materialized and verified; dump identity and counts. |

`serverInfo.name` is `mitomap-link`, and leaf tool names are intentionally **unprefixed** per
the GeneFoundry Tool-Naming Standard v1. The canonical gateway namespace token is
`mitomap`: behind [`genefoundry-router`](https://github.com/berntpopp/genefoundry-router)
these surface as `mitomap_<tool>` (e.g. `mitomap_get_variant`).

Every response carries `_meta.next_commands` and `recommended_citation`, and honours
`response_mode ∈ {minimal, compact, standard, full}` (default `compact`). See
[Usage](docs/usage.md).

## Data & provenance

- **Source** — the MITOMAP daily PostgreSQL dump
  (`https://mitomap.org/downloads/mitomap.dump.sql.gz`), parsed as text (never restored or
  executed) into a derived SQLite snapshot of the mutation, polymorphism, GenBank-count,
  reference and locus tables. Submitter contact tables are never read. See [Data](docs/data.md).
- **Pin** — an immutable, attested GitHub data release `data-mitomap-<sha16>`; its manifest
  records the dump's SHA-256 and Last-Modified. The app serves nothing unless the bytes
  match `mitomap_link/store/pin.py`.
- **Refresh** — none at runtime: a new snapshot is a `data-release` workflow run, a reviewed
  pin bump, and a new release of this server.
- **Licence** — MITOMAP content is **CC BY 3.0**; redistribution of the derived snapshot is
  the repository owner's determination (`release/data-authorization.json`), not a MITOMAP
  approval.
- **Citation** — MITOMAP: A Human Mitochondrial Genome Database. https://www.mitomap.org.
  Lott MT, Leipzig JN, Derbeneva O, Xie HM, Chalkia D, Sarmady M, Procaccio V, Wallace DC.
  mtDNA Variation and Analysis Using MITOMAP and MITOMASTER. *Curr Protoc Bioinformatics*.
  2013;44:1.23.1-26. doi:10.1002/0471250953.bi0123s44.

## Documentation

- [Usage](docs/usage.md) — workflows, notations, status/plasmy/GenBank semantics, `response_mode`.
- [Configuration](docs/configuration.md) — every `MITOMAP_LINK_*` variable, the transports, and the Host / Origin / CORS boundary.
- [Data](docs/data.md) — the dump, the derived snapshot, licence, and how to cut a new data release.
- [Deployment](docs/deployment.md) — the hardened container, the init sidecar, and the release flow.

## Contributing

See [`AGENTS.md`](AGENTS.md) for engineering conventions. `make ci-local` is the
definition-of-done gate: format, lint, line budget, README standard, mypy strict, and tests.

## License

[MIT](LICENSE) © mitomap-link contributors. MITOMAP **data** are CC BY 3.0; cite them as
above.
