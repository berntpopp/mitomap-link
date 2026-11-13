"""FastAPI host for mitomap-link (thin: health + service info + data bootstrap)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mitomap_link import __version__
from mitomap_link.buildinfo import build_info
from mitomap_link.config import settings
from mitomap_link.exceptions import DataUnavailableError
from mitomap_link.logging_config import configure_logging
from mitomap_link.mcp.service_adapters import get_repository, observed_identity, peek_repository
from mitomap_link.store.identity import expected_identity

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Backends are unauthenticated by design (edge auth lives at the router), so CORS
# credentials are meaningless. Keep them off; wiring them back on with a wildcard
# origin is a footgun the startup guard below rejects.
_CORS_ALLOW_CREDENTIALS = False


def _validate_cors(origins: list[str], allow_credentials: bool) -> None:
    """Fail closed on the unsafe wildcard-origin + credentials CORS combination.

    An unauthenticated backend holds no cookies/session, so credentials are
    pointless; combined with a ``*`` origin they are also forbidden by the CORS
    spec. Reject that combination at startup rather than silently shipping a
    permissive policy.
    """
    if allow_credentials and "*" in origins:
        raise ValueError(
            "CORS misconfiguration: allow_credentials=True with a wildcard '*' "
            "origin. Backends are unauthenticated by design; disable credentials "
            "or pin explicit origins."
        )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Open and verify the pinned snapshot (a failure is retried on the next tool call)."""
    logger = configure_logging()
    logger.info("mitomap-link starting", host=settings.host, port=settings.port)
    try:
        await get_repository()
        logger.info("mitomap snapshot verified", release_tag=settings.data.release_tag)
    except DataUnavailableError as exc:
        logger.warning("mitomap snapshot unavailable; will retry on use", error=exc.message)
    yield
    logger.info("mitomap-link shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="mitomap-link",
        description="MCP/API server for MITOMAP mitochondrial DNA variants.",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    _validate_cors(settings.cors_origins, _CORS_ALLOW_CREDENTIALS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=_CORS_ALLOW_CREDENTIALS,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, Any]:
        """Liveness probe (reports build provenance for deploy checks)."""
        return {
            "status": "ok",
            "service": "mitomap-link",
            "transport": "streamable-http-stateless",
            "data_loaded": peek_repository() is not None,
            # Fleet runtime-v1 data identity: the configured pin and the identity proven
            # when the served snapshot was opened (null until verified).
            "release_identity": {
                "schema_version": 1,
                "data_identity": {
                    "expected": expected_identity(settings.data),
                    "actual": observed_identity(),
                },
            },
            **build_info(),
        }

    @app.get("/")
    async def root() -> dict[str, Any]:
        """Service information."""
        return {
            "name": "mitomap-link",
            "version": __version__,
            "data_source": f"MITOMAP daily dump, data release {settings.data.release_tag}",
            "mcp_endpoint": settings.mcp_path,
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
