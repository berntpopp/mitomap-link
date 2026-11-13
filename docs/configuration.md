# Configuration

Every setting is an environment variable with the `MITOMAP_LINK_` prefix. Nested
config uses a **double underscore**, e.g. `MITOMAP_LINK_DATA__LOCAL_DATABASE`. Copy
[`.env.example`](../.env.example) to `.env` to start; everything below is optional
and shown with the default that `mitomap_link/config.py` actually sets.

The tables below are **exhaustive, and a test says so**: `tests/unit/test_docs_config.py`
enumerates every field of `ServerSettings` (including the nested `DATA__`
model) and fails if this page omits one — or documents one that no longer exists.

## Server

| Variable | Default | Purpose |
|----------|---------|---------|
| `MITOMAP_LINK_HOST` | `127.0.0.1` | Bind address. |
| `MITOMAP_LINK_PORT` | `8000` | Bind port (1024–65535). |
| `MITOMAP_LINK_TRANSPORT` | `unified` | `unified` \| `http` \| `stdio`. |
| `MITOMAP_LINK_MCP_PATH` | `/mcp` | MCP endpoint path. |
| `MITOMAP_LINK_ALLOWED_HOSTS` | `["localhost","127.0.0.1","::1"]` | JSON list of **exact** `Host` values admitted. |
| `MITOMAP_LINK_ALLOWED_ORIGINS` | `[]` | JSON list of **exact** browser `Origin` values admitted. |
| `MITOMAP_LINK_CORS_ORIGINS` | `["http://localhost:3000","http://127.0.0.1:3000"]` | JSON list of origins that receive CORS response headers. |
| `MITOMAP_LINK_LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` \| `CRITICAL`. |
| `MITOMAP_LINK_LOG_FORMAT` | `console` | `console` \| `json`. |
| `MITOMAP_LINK_RELOAD` | `false` | Uvicorn auto-reload. Development only — never enable in a container. |

## MITOMAP data release

The server serves one derived SQLite snapshot of the MITOMAP daily dump, published as an
immutable GitHub data release and pinned in `mitomap_link/store/pin.py` (which
`container-release.json` must match) — see [Data](data.md). The `mitomap-data-init`
container downloads and verifies it into `REFERENCE_ROOT`; the app re-verifies it and
serves nothing until it matches. Leave the pin variables at their defaults in
production: overriding them serves a release this build was not reviewed against.

| Variable | Default | Purpose |
|----------|---------|---------|
| `MITOMAP_LINK_DATA__RELEASE_TAG` | the pinned `data-mitomap-<sha16>` tag | Data release to serve. |
| `MITOMAP_LINK_DATA__COMPRESSED_SHA256` | the pinned digest | SHA-256 of `mitomap.sqlite.gz` (the fleet `data.digest`). |
| `MITOMAP_LINK_DATA__EXPANDED_SHA256` | the pinned digest | SHA-256 of the expanded `mitomap.sqlite`. |
| `MITOMAP_LINK_DATA__BUNDLE_URL` | the pinned release asset URL | Download URL (must be a `github.com/berntpopp/mitomap-link/releases/` URL). |
| `MITOMAP_LINK_DATA__REFERENCE_ROOT` | `/data` | Volume the snapshot is materialized into (`<root>/<compressed_sha256>/`). |
| `MITOMAP_LINK_DATA__LOCAL_DATABASE` | unset | **Development only**: serve this SQLite file without release verification (health then reports no observed identity). |
| `MITOMAP_LINK_DATA__MAX_COMPRESSED_BYTES` | `67108864` (64 MiB) | Download-size cap for the bundle. |
| `MITOMAP_LINK_DATA__MAX_EXPANDED_BYTES` | `268435456` (256 MiB) | Size cap for the expanded SQLite. |
| `MITOMAP_LINK_DATA__DOWNLOAD_TIMEOUT` | `300.0` | HTTP timeout (s) for the init download. |

## The Host / Origin / CORS boundary

HTTP deployments enforce **exact** `Host` and `Origin` allowlists on every route.
Wildcards are not accepted. Three rules that are easy to get wrong:

1. **Add the public hostname.** `MITOMAP_LINK_ALLOWED_HOSTS` must contain the exact
   public reverse-proxy hostname *in addition to* the loopback defaults, or every
   proxied request is rejected.
2. **`MITOMAP_LINK_ALLOWED_ORIGINS` defaults to `[]`, which admits requests that carry
   no `Origin` header at all** — that is what lets non-browser MCP clients (Claude
   Code, `curl`) work out of the box. It does *not* mean "allow any origin".
3. **Request validation and CORS are separate policies, and neither widens the
   other.** A browser deployment must list its origin in **both**
   `MITOMAP_LINK_ALLOWED_ORIGINS` (admission) and `MITOMAP_LINK_CORS_ORIGINS` (response
   headers). Note their defaults differ: admission is empty, CORS ships with the
   two localhost:3000 dev origins.

## Transports

- **`unified`** (default) — FastAPI `/health` plus the MCP endpoint at `/mcp` on one
  port. `make dev`.
- **`http`** — HTTP transport without the unified REST host.
- **`stdio`** — `make mcp-serve` (`uv run python mcp_server.py`), used by Claude
  Desktop. On stdio **stdout is reserved for the protocol** — logs go to stderr.

Register the HTTP server with Claude Code:

```bash
claude mcp add --transport http mitomap-link --scope user http://127.0.0.1:8000/mcp
```
