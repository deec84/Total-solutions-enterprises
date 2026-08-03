"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.modules.observability.runtime import ObservabilityRuntime, build_observability_runtime
from app.presentation.api.errors import (
    http_exception_handler,
    starlette_http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.presentation.api.router import api_router
from app.shared.config import get_settings
from app.shared.http_security import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Own process-level resources; database and telemetry hooks are added by phase."""
    yield


def create_app(observability: ObservabilityRuntime | None = None) -> FastAPI:
    """Build an isolated application instance for production and tests."""
    settings = get_settings()
    logging.basicConfig(level=settings.log_level, format="%(message)s")
    logging.getLogger("parkshield.http").setLevel(settings.log_level)
    logging.getLogger("parkshield.integrations").setLevel(settings.log_level)
    logging.getLogger("parkshield.analytics").setLevel(settings.log_level)
    observability = observability or build_observability_runtime(settings)
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
        observability=observability,
    )
    application.add_exception_handler(HTTPException, http_exception_handler)
    application.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.add_exception_handler(Exception, unhandled_exception_handler)
    application.state.observability = observability
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application
