"""Transport security, correlation IDs, and privacy-safe structured access logs."""

import json
import logging
import re
import time
from typing import cast
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, production: bool = False) -> None:
        self._app = app
        self._production = production

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        request_id = self._request_id(scope)
        scope.setdefault("state", {})["request_id"] = request_id
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
                if self._production:
                    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            await send(message)

        try:
            await self._app(scope, receive, send_with_headers)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logging.getLogger("parkshield.http").info(
                json.dumps(
                    {
                        "event": "http_request_completed",
                        "request_id": request_id,
                        "method": scope["method"],
                        "path": scope["path"],
                        "status_code": response_status,
                        "duration_ms": duration_ms,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )

    @staticmethod
    def _request_id(scope: Scope) -> str:
        for key, value in scope["headers"]:
            if key.lower() != b"x-request-id" or not value:
                continue
            candidate = cast(bytes, value)[:128].decode("ascii", errors="ignore")
            if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", candidate):
                return candidate
        return str(uuid4())
