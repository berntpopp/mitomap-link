# AGENTS.md — engineering conventions for mitomap-link

Guidance for AI agents and contributors working in this repo. `mitomap-link` is a
sibling of `uniprot-link`, `gnomad-link`, `gencc-link`, `clingen-link`; keep it
consistent with those.

## Golden rules

1. **Run the gate before claiming done:** `make ci-local`
   (format-check → lint → line-budget → README standard → mypy strict → tests).
   All must pass.
2. **Per-file line budget: 500 lines** (`make lint-loc`). Split modules that grow.
3. **mypy is strict.** Fully type new code; no untyped defs.
4. **stdout is sacred on stdio.** Logs go to stderr; never `print` to stdout in
   server/library code (the CLI is the only place `print` is allowed).

## Make targets

| Target | What it does |
|--------|--------------|
| `make install` | `uv sync --group dev`. |
| `make dev` / `make mcp-serve` | Unified REST + MCP server / stdio MCP server. |
| `make check` | `format` + `lint`. |
| `make typecheck` | `mypy --strict`. |
| `make test` / `make test-fast` / `make test-cov` | Unit tests / parallel / with coverage. |
| `make lint-loc` / `make lint-readme` | 500-line budget / GeneFoundry README Standard v1. |
| `make ci-local` | The definition-of-done gate. |

`docs/` holds what a README must not carry: `configuration.md` (every
`MITOMAP_LINK_*` var, the Host/Origin/CORS boundary), `data.md` (the dump, the derived
snapshot, licence, data releases), `deployment.md`, `usage.md`.

## Architecture invariants (do not break)

- **One data release, pinned.** `store/pin.py` names the `data-mitomap-<sha16>` GitHub
  data release this build serves; `container-release.json` `data.release_tag`/`digest`
  must match (`tests/unit/test_release_contract.py`). The init container
  (`mitomap-link-data materialize`) verifies both digests before selecting it; the app
  re-verifies and fails closed. New data = `data-release.yml` run + reviewed pin bump +
  app release (see `docs/data.md`).
- **The MITOMAP dump is untrusted input.** `ingest/dump.py` decodes COPY data for an
  allowlist of tables and never restores or executes the dump. Never read the submitter
  contact tables (`unpublished`, `submitted_variant*`). Builds stay deterministic (no
  wall-clock value in the snapshot).
- **Report the source, never reinterpret it.** MITOMAP status, plasmy flags and disease
  text stay verbatim; missing stays null; nothing is inferred (no heteroplasmy, no
  haplogroup, no pathogenicity call). Only rCRS (NC_012920.1) is accepted
  (`variant_ids.py`); other mitochondrial references are rejected, never remapped.
- **Upstream prose is fenced** (`mcp/untrusted_content.py`, Response-Envelope v1.1):
  `disease` and `status_note` at every mode, reference titles (get_variant only, ≤50 per
  record) at `response_mode=standard|full`; search rows carry PMIDs, never titles. Never surface an upstream string
  unfenced unless it passes an identifier grammar.
- **The MCP layer owns the envelope.** `mcp/envelope.run_mcp_tool` injects
  `success`/`_meta`, converts exceptions into typed error envelopes with `isError`, and
  never interpolates caller input into a message. Error codes are the closed fleet enum.
- **Every response carries `_meta.next_commands`**; build them in
  `mcp/next_commands.py` from validated identifiers only.
- **Tool descriptions end with `Signature: tool(args...)`**; every required parameter
  carries `examples` (the behaviour probe builds its calls from them).
- Keep `mcp/capabilities.TOOLS`, the README `## Tools` table and `docs/usage.md` in sync
  with the registered tools (tests assert it).

### Fleet deploy contract

- `docker/docker-compose.npm.yml` is the file the fleet controller
  (`strato_v6_docker_npm`) deploys and validates. Every service there declares
  `user: "<uid>:<gid>"` numerically — this image's own uid:gid from
  `docker/Dockerfile` (currently `10001:10001`), never copied from a sibling `-link`
  repo.
- `user` must **not** appear in the Compose files listed in
  `container-release.json` (`docker/docker-compose.yml`,
  `docker/docker-compose.prod.yml`) — the shared release gate
  (`container_release.py validate-compose`) forbids it there.
- Both rules are enforced by `tests/unit/test_deploy_overlay_user.py`.
- `container-release.json` declares `service.deployed_compose_files:
  ["docker/docker-compose.npm.yml"]` — the exact file the controller deploys.
  Both reusable-workflow pins (`.github/workflows/container-ci.yml`,
  `.github/workflows/container-release.yml`) must track the same
  `genefoundry-router` revision: the shared `_container-release.yml` workflow
  runs `container_release.py validate-deployed-overlay` against the declared
  file before every release, and `_container-ci.yml` loads the same
  `ReleaseConfig` schema from its own pin to validate this JSON, so an older
  pin there rejects new fields.
- **Release checklist** (fleet controller pulls a tagged, attested image — it
  never builds from source): bump `pyproject.toml`, `uv lock`, add a
  `CHANGELOG.md` heading `## [x.y.z] - YYYY-MM-DD`, bump `CITATION.cff`
  `version:` (the file is generated — see its header comment; `date-released`
  is **not** touched by this repo's release process, it is regenerated
  externally by `genefoundry-router`'s `make citation-write`), tag `vx.y.z`,
  then approve the `release` environment gate via
  `gh api repos/berntpopp/mitomap-link/actions/runs/<id>/pending_deployments`
  (may need approving twice; `status: waiting` is the gate).

## Testing

- Unit tests are network-free: `tests/conftest.py` builds a snapshot from the tiny dump
  excerpt `tests/fixtures/mitomap.dump.excerpt.sql` (CC BY 3.0). Mock HTTP with `respx`.
- Call tools through the **real facade** and read `structured_content`.
- `tests/conformance/` vendors the router's transport, behaviour and contract-truth
  probes byte-identical; the live probes run in `conformance.yml`.

## Adding a tool

1. Tool in `mcp/tools/<area>.py`, registered from `tools/__init__.py` and `mcp/facade.py`.
2. Projection in `mcp/shaping.py`; chain builder in `mcp/next_commands.py`.
3. Add to `capabilities.TOOLS`, the README `## Tools` table and `docs/usage.md`.
4. Unit + facade tests; run the behaviour probe locally against `make dev`.
