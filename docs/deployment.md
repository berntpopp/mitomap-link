# Deployment

`mitomap-link` runs as two containers from one image. `mitomap-data-init` downloads the
pinned data release (`mitomap.sqlite.gz`, ~5 MB) from GitHub, verifies its compressed and
expanded SHA-256, and atomically selects it in the named volume `mitomap-reference`, then
exits. The app starts only after the init completed successfully, mounts the volume
read-only, re-verifies the snapshot, and serves it. There is no refresh job: a new
snapshot is a data release, a reviewed pin bump and a new application release
([Data](data.md)).

## Container

The image follows the GeneFoundry Container & Deployment Hardening Standard v1:

- non-root `10001:10001`, read-only root filesystem, `/tmp` as a `noexec,nosuid` tmpfs;
- `cap_drop: ALL`, `no-new-privileges`, `init`, memory/CPU/PID limits;
- digest-pinned base image, code-only (the dataset is never baked in; no `VOLUME`);
- expose-only behind the reverse proxy (`ports: !reset []` in the production overlays).

Egress: only the init container needs it, to `github.com` and its release-asset hosts
(redirects to any other host are refused). The app needs none.

```bash
# Local
make docker-build && make docker-up

# Production (digest-pinned image, no build)
MITOMAP_LINK_IMAGE=ghcr.io/berntpopp/mitomap-link@sha256:<digest> \
  docker compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d

# Fleet (Nginx Proxy Manager overlay — what the fleet controller deploys)
docker compose -f docker/docker-compose.npm.yml --env-file .env.docker up -d
```

The public hostname (`mitomap-link.genefoundry.org`) is already in
`MITOMAP_LINK_ALLOWED_HOSTS` in both production overlays. The backend is unauthenticated
by design: expose it only through the reverse proxy / router, never directly.

## Releases

A protected `vX.Y.Z` tag runs `.github/workflows/container-release.yml`, which calls the
router's reusable `_container-release.yml` (pinned by commit). It builds one
`linux/amd64` image, inspects every layer, runs the hardened container plus MCP checks,
scans it, attests provenance and an SBOM, and creates the immutable GitHub Release. The
`release` environment gate requires an owner approval. Never create a release by hand.

Data releases are separate: `.github/workflows/data-release.yml` (dispatch on `main`)
waits on the `data-release` environment (owner approval, `main` only); see [Data](data.md).

Health: `GET /health` returns `status`, `version`, `git_sha`, `built_at`, `data_loaded`
and `release_identity` (fleet runtime-v1: the pinned `expected` release and the `actual`
one proven when the snapshot was opened; the release gate requires them to match).
`get_diagnostics` adds the dump identity, MITOMAP edit dates and record counts.
