"""Transport security, correlation IDs, and privacy-safe structured access logs."""

import json
import logging
import re
import time
from typing import cast
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.modules.observability.redaction import (
    correlation_id_context,
    request_id_context,
    trace_id_context,
)
from app.modules.observability.runtime import ObservabilityRuntime, RequestObservation
from app.modules.observability.tracing import trace_context

_SAFE_ID = re.compile(r"[A-Za-z0-9._:-]{1,128}")


def _request_category(path: str, method: str) -> str:
    if method == "POST" and path in {
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/mfa/verify",
    }:
        return "authentication"
    if method == "POST" and path.endswith("/imports"):
        return "municipal_import"
    if method == "POST" and path == "/api/v1/signs/scan":
        return "sign_analysis"
    if path.startswith("/api/v1/parking/") or path == "/api/v1/ai/parking-assistant":
        return "parking_score"
    if method != "GET" and path.startswith("/api/v1/reports"):
        return "community"
    if method == "POST" and path == "/api/v1/billing/purchases/verify":
        return "billing"
    if path.startswith("/api/v1/health/"):
        return "health"
    return "other"


class SecurityHeadersMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        production: bool = False,
        observability: ObservabilityRuntime | None = None,
    ) -> None:
        self._app = app
        self._production = production
        self._observability = observability

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        request_id = self._request_id(scope)
        correlation_id = self._header_id(scope, b"x-correlation-id") or request_id
        incoming_traceparent = self._header(scope, b"traceparent")
        context = trace_context(incoming_traceparent)
        state = scope.setdefault("state", {})
        state["request_id"] = request_id
        state["correlation_id"] = correlation_id
        state["trace_id"] = context.trace_id
        category = _request_category(scope["path"], scope["method"])
        span = (
            self._observability.start_request_span(
                context,
                {
                    "http.request.method": scope["method"],
                    "parkshield.request.category": category,
                },
            )
            if self._observability is not None
            else None
        )
        if span is not None:
            context = span.context
            state["trace_id"] = context.trace_id
        request_token = request_id_context.set(request_id)
        correlation_token = correlation_id_context.set(correlation_id)
        trace_token = trace_id_context.set(context.trace_id)
        started = time.perf_counter()
        response_status = 500

        async def send_with_headers(message: Message) -> None:
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = int(message["status"])
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
                headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
                headers["X-Request-ID"] = request_id
                headers["X-Correlation-ID"] = correlation_id
                headers["traceparent"] = context.traceparent
                if self._production:
                    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            await send(message)

        try:
            await self._app(scope, receive, send_with_headers)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            if self._observability is not None:
                self._observability.observe_request(
                    RequestObservation(
                        scope["method"], category, response_status, duration_ms
                    )
                )
            if span is not None:
                span.end("error" if response_status >= 500 else "ok")
            logging.getLogger("parkshield.http").info(
                json.dumps(
                    {
                        "event": "http_request_completed",
                        "service": (
                            self._observability.service_name
                            if self._observability is not None
                            else "parkshield-api"
                        ),
                        "request_id": request_id,
                        "correlation_id": correlation_id,
                        "trace_id": context.trace_id,
                        "method": scope["method"],
                        "category": category,
                        "status_code": response_status,
                        "duration_ms": duration_ms,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
            request_id_context.reset(request_token)
            correlation_id_context.reset(correlation_token)
            trace_id_context.reset(trace_token)

    @staticmethod
    def _request_id(scope: Scope) -> str:
        return SecurityHeadersMiddleware._header_id(scope, b"x-request-id") or str(
            uuid4()
        )

    @staticmethod
    def _header_id(scope: Scope, header_name: bytes) -> str | None:
        value = SecurityHeadersMiddleware._header(scope, header_name)
        if value is None:
            return None
        candidate = value[:128]
        return candidate if _SAFE_ID.fullmatch(candidate) else None

    @staticmethod
    def _header(scope: Scope, header_name: bytes) -> str | None:
        for key, value in scope["headers"]:
            if key.lower() == header_name and value:
                return cast(bytes, value)[:256].decode("ascii", errors="ignore")
        return None
