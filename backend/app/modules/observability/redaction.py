"""Fail-closed field filtering for logs, traces, metrics, and analytics."""

import json
import logging
from collections.abc import Mapping
from contextvars import ContextVar

from app.modules.observability.ports import Scalar

request_id_context: ContextVar[str] = ContextVar("request_id", default="unknown")
correlation_id_context: ContextVar[str] = ContextVar("correlation_id", default="unknown")
trace_id_context: ContextVar[str] = ContextVar("trace_id", default="unknown")

_PROHIBITED_FRAGMENTS = frozenset(
    {
        "authorization",
        "cookie",
        "credential",
        "email",
        "latitude",
        "longitude",
        "location",
        "message",
        "password",
        "payload",
        "photo",
        "receipt",
        "secret",
        "signed",
        "token",
        "vin",
    }
)


def is_prohibited_field(name: str) -> bool:
    normalized = name.casefold().replace("-", "_")
    return any(fragment in normalized for fragment in _PROHIBITED_FRAGMENTS)


def allowlisted_fields(
    values: Mapping[str, object], allowed: frozenset[str]
) -> dict[str, Scalar]:
    """Return bounded scalar values only; unknown or sensitive keys are dropped."""
    result: dict[str, Scalar] = {}
    for key, value in values.items():
        if key not in allowed or is_prohibited_field(key) or not isinstance(value, Scalar):
            continue
        if isinstance(value, str):
            result[key] = value[:80]
        else:
            result[key] = value
    return result


def log_integration_failure(provider: str, operation: str, error: Exception) -> None:
    """Record classification and context, never exception text or provider payloads."""
    logging.getLogger("parkshield.integrations").warning(
        json.dumps(
            {
                "event": "external_integration_failed",
                "provider": provider[:40],
                "operation": operation[:60],
                "error_type": type(error).__name__[:80],
                "request_id": request_id_context.get(),
                "correlation_id": correlation_id_context.get(),
                "trace_id": trace_id_context.get(),
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
