# Docker

```bash
make docker-build       # build the image
make docker-up          # start (prints the MCP URL + Claude Code command)
make docker-logs        # follow logs
make docker-down        # stop
```

`mitomap-data-init` (the same image, `mitomap-link-data materialize`) downloads the pinned
data release (~5 MB) from GitHub, verifies both digests and selects it in the
`mitomap-reference` volume, then exits; the app mounts that volume read-only. There is no
refresh job: a new snapshot ships as a new data release plus a new image release.

## Ports

The host port defaults to `8000`; override with `MITOMAP_LINK_HOST_PORT` (e.g. in
`docker/.env`). MCP endpoint: `http://127.0.0.1:<port>/mcp`. Health:
`http://127.0.0.1:<port>/health`.
