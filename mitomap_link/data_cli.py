"""``mitomap-link-data``: build a data release (CI) or materialize one (init container)."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from mitomap_link.config import settings
from mitomap_link.exceptions import DataUnavailableError
from mitomap_link.ingest.build import SourceInfo, build_database
from mitomap_link.ingest.release import package_release
from mitomap_link.store.materialize import materialize

SOURCE_URL = "https://mitomap.org/downloads/mitomap.dump.sql.gz"


def _build(args: argparse.Namespace) -> int:
    dump = Path(args.dump)
    digest = hashlib.sha256()
    with dump.open("rb") as fh:
        while chunk := fh.read(1 << 20):
            digest.update(chunk)
    source = SourceInfo(SOURCE_URL, digest.hexdigest(), dump.stat().st_size, args.last_modified)
    with tempfile.TemporaryDirectory() as tmp:
        database = Path(tmp) / "mitomap.sqlite"
        with gzip.open(dump, "rt", encoding="utf-8") as lines:
            counts = build_database(lines, database, source)
        manifest = package_release(
            database,
            Path(args.output),
            source,
            counts,
            revision=args.revision,
            authorization=Path(args.authorization),
        )
    print(json.dumps(manifest, indent=2, sort_keys=True))  # noqa: T201
    return 0


def _materialize(_args: argparse.Namespace) -> int:
    try:
        target = materialize(settings.data)
    except DataUnavailableError as exc:
        print(f"materialize failed: {exc.message}", file=sys.stderr)  # noqa: T201
        return 1
    print(f"materialized {settings.data.release_tag} at {target}")  # noqa: T201
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run one subcommand."""
    parser = argparse.ArgumentParser(prog="mitomap-link-data")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="Build release assets from one downloaded dump.")
    build.add_argument("--dump", required=True, help="Path to mitomap.dump.sql.gz.")
    build.add_argument("--last-modified", required=True, help="HTTP Last-Modified of the dump.")
    build.add_argument("--output", required=True, help="New directory for the release assets.")
    build.add_argument("--revision", required=True, help="Source commit of this builder.")
    build.add_argument("--authorization", required=True, help="Redistribution record JSON.")
    build.set_defaults(func=_build)
    sub.add_parser("materialize", help="Fetch and verify the pinned release.").set_defaults(
        func=_materialize
    )
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
