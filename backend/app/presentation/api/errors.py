"""Stable, privacy-safe HTTP error contract for public API consumers."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

ERROR_CONTRACT_VERSION: Literal["1"] = "1"


class ErrorCode(StrEnum):
    """Initial public error-code catalog. Values are backward-compatible API surface."""

    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    SESSION_INVALID = "SESSION_INVALID"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CONFLICT = "CONFLICT"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NO_VERIFIED_COVERAGE = "NO_VERIFIED_COVERAGE"
    STALE_DATA = "STALE_DATA"
    LOCATION_PRECISION_INSUFFICIENT = "LOCATION_PRECISION_INSUFFICIENT"
    DECISION_INDETERMINATE = "DECISION_INDETERMINATE"


class ErrorDetail(BaseModel):
    """Allowlisted validation metadata; never includes submitted values or messages."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.\[\]-]+$")
    code: Literal["MISSING_FIELD", "INVALID_FIELD"]


class ErrorResponse(BaseModel):
    """Versioned envelope returned for every handled API error."""

    model_config = ConfigDict(extra="forbid")

    version: Literal["1"] = ERROR_CONTRACT_VERSION
    code: ErrorCode
    message: str = Field(min_length=1, max_length=160)
    correlation_id: str = Field(min_length=1, max_length=128)
    details: list[ErrorDetail] | None = None


_STATUS_CODES: dict[int, tuple[ErrorCode, str]] = {
    status.HTTP_400_BAD_REQUEST: (ErrorCode.INVALID_REQUEST, "Invalid request."),
    status.HTTP_401_UNAUTHORIZED: (
        ErrorCode.AUTHENTICATION_REQUIRED,
        "Authentication is required.",
    ),
    status.HTTP_403_FORBIDDEN: (ErrorCode.AUTHORIZATION_DENIED, "Access is denied."),
    status.HTTP_404_NOT_FOUND: (ErrorCode.RESOURCE_NOT_FOUND, "Resource not found."),
    status.HTTP_409_CONFLICT: (ErrorCode.CONFLICT, "Request conflicts with current state."),
    status.HTTP_413_CONTENT_TOO_LARGE: (
        ErrorCode.PAYLOAD_TOO_LARGE,
        "Payload is too large.",
    ),
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: (
        ErrorCode.UNSUPPORTED_MEDIA_TYPE,
        "Unsupported media type.",
    ),
    status.HTTP_422_UNPROCESSABLE_CONTENT: (ErrorCode.VALIDATION_FAILED, "Invalid request."),
    status.HTTP_429_TOO_MANY_REQUESTS: (ErrorCode.RATE_LIMITED, "Too many requests."),
    status.HTTP_503_SERVICE_UNAVAILABLE: (
        ErrorCode.SERVICE_UNAVAILABLE,
        "Service is temporarily unavailable.",
    ),
}


def _correlation_id(request: Request) -> str:
    candidate = getattr(request.state, "correlation_id", None)
    return candidate if isinstance(candidate, str) and candidate else str(uuid4())


def _authentication_code(request: Request) -> tuple[ErrorCode, str]:
    if request.url.path == "/api/v1/auth/login":
        return ErrorCode.AUTHENTICATION_FAILED, "Authentication failed."
    if request.url.path in {"/api/v1/auth/refresh", "/api/v1/auth/logout"}:
        return ErrorCode.SESSION_INVALID, "Session is invalid or expired."
    return _STATUS_CODES[status.HTTP_401_UNAUTHORIZED]


def error_for_status(request: Request, status_code: int) -> tuple[ErrorCode, str]:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return _authentication_code(request)
    return _STATUS_CODES.get(status_code, (ErrorCode.INTERNAL_ERROR, "Unexpected server error."))


def _response(
    request: Request,
    status_code: int,
    code: ErrorCode,
    message: str,
    details: list[ErrorDetail] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        code=code,
        message=message,
        correlation_id=_correlation_id(request),
        details=details or None,
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(exclude_none=True),
        headers=headers,
    )


def _safe_headers(headers: Mapping[str, str] | None) -> dict[str, str] | None:
    if not headers:
        return None
    retry_after = headers.get("Retry-After")
    return {"Retry-After": retry_after} if retry_after and retry_after.isdigit() else None


async def http_exception_handler(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, HTTPException)
    code, message = error_for_status(request, error.status_code)
    return _response(
        request,
        error.status_code,
        code,
        message,
        headers=_safe_headers(error.headers),
    )


async def starlette_http_exception_handler(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, StarletteHTTPException)
    code, message = error_for_status(request, error.status_code)
    return _response(
        request,
        error.status_code,
        code,
        message,
        headers=_safe_headers(error.headers),
    )


def _validation_details(errors: Iterable[dict[str, Any]]) -> list[ErrorDetail]:
    details: list[ErrorDetail] = []
    for error in errors:
        location = error.get("loc", ())
        field = ".".join(str(item) for item in location if item not in {"body", "query", "path"})
        if not field:
            field = "request"
        error_type = str(error.get("type", ""))
        detail_code: Literal["MISSING_FIELD", "INVALID_FIELD"] = (
            "MISSING_FIELD" if error_type == "missing" else "INVALID_FIELD"
        )
        details.append(ErrorDetail(field=field[:128], code=detail_code))
    return details[:20]


async def validation_exception_handler(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, RequestValidationError)
    return _response(
        request,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        ErrorCode.VALIDATION_FAILED,
        "Invalid request.",
        _validation_details(error.errors()),
    )


async def unhandled_exception_handler(request: Request, error: Exception) -> JSONResponse:
    logging.getLogger("parkshield.http").error(
        "unhandled_api_error correlation_id=%s exception_type=%s",
        _correlation_id(request),
        type(error).__name__,
    )
    return _response(
        request,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.INTERNAL_ERROR,
        "Unexpected server error.",
    )


def error_responses() -> dict[int | str, dict[str, object]]:
    """OpenAPI declarations inherited by every public API route."""

    responses: dict[int | str, dict[str, object]] = {}
    for status_code, (_, description) in _STATUS_CODES.items():
        responses[status_code] = {"description": description, "model": ErrorResponse}
    responses[status.HTTP_500_INTERNAL_SERVER_ERROR] = {
        "description": "Unexpected server error.",
        "model": ErrorResponse,
    }
    return responses
