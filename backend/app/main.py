"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.presentation.api.router import api_router
from app.shared.config import get_settings
from app.shared.http_security import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Own process-level resources; database and telemetry hooks are added by phase."""
    yield


def create_app() -> FastAPI:
    """Build an isolated application instance for production and tests."""
    settings = get_settings()
    logging.getLogger("parkshield.http").setLevel(settings.log_level)
    application = FastAPI(
        title="ParkShield AI API",
        version="0.1.0",
        description="Parking intelligence with explicit source provenance.",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    application.add_middleware(
        SecurityHeadersMiddleware,
        production=settings.environment == "production",
    )
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application
