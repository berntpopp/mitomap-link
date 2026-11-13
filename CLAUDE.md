# CLAUDE.md

This file guides Claude Code when working in this repository.

**Read [`AGENTS.md`](AGENTS.md) first** — it holds the engineering conventions,
architecture invariants, and the definition of done. They apply in full here.

## TL;DR

- Run `make ci-local` before claiming anything is done.
- The server serves one derived MITOMAP SQLite snapshot from a pinned GitHub data
  release (`mitomap_link/store/pin.py`), materialized and verified by an init container.
- The MITOMAP dump is untrusted: parsed as COPY text, never restored or executed.
- Report MITOMAP status/plasmy/disease verbatim; missing stays null; rCRS only; fence
  reference titles; no pathogenicity call, no haplogroup, no heteroplasmy inference.
- Files stay under 500 lines; logs go to stderr.

## Common commands

```bash
make install          # uv sync --group dev
make dev-data         # data/dev.sqlite from the test fixture
make dev              # unified REST + MCP server (set MITOMAP_LINK_DATA__LOCAL_DATABASE)
make test             # unit tests
make ci-local         # full local gate
```

## Layout

`mitomap_link/{config,constants,exceptions,variant_ids,data_cli,logging_config,buildinfo,safe_fields}.py`
· `ingest/` (dump reader, snapshot builder, release packaging) · `store/` (pin,
materialize, identity, repository) · `mcp/` (envelope, shaping, untrusted_content, next_commands, capabilities,
middleware, notfound_guard, tools, facade) · `server.py` / `mcp_server.py`.
