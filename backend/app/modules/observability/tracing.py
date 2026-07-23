"""W3C trace context and provider-neutral span adapters."""

import re
import secrets
from collections.abc import Mapping
from datetime import UTC, datetime
from threading import Lock

from app.modules.observability.domain import SpanRecord, TraceContext
from app.modules.observability.ports import OpenTelemetrySpanLike, OpenTelemetryTracerLike, Scalar
from app.modules.observability.redaction import log_integration_failure

_TRACEPARENT = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-(00|01)$")


def trace_context(header: str | None) -> TraceContext:
    if header:
        match = _TRACEPARENT.fullmatch(header.strip().casefold())
        if match and match.group(1) != "0" * 32 and match.group(2) != "0" * 16:
            return TraceContext(
                match.group(1),
                secrets.token_hex(8),
                match.group(3) == "01",
                match.group(2),
            )
    return TraceContext(secrets.token_hex(16), secrets.token_hex(8), True)


class _MemorySpan:
    def __init__(
        self,
        owner: "InMemoryTracing",
        name: str,
        context: TraceContext,
        attributes: Mapping[str, Scalar],
    ) -> None:
        self._owner = owner
        self._name = name
        self._context = context
        self._attributes = dict(attributes)
        self._started_at = datetime.now(UTC)
        self._ended = False

    @property
    def context(self) -> TraceContext:
        return self._context

    def end(self, status: str, error_type: str | None = None) -> None:
        if self._ended:
            return
        self._ended = True
        self._owner._record(
            SpanRecord(
                self._name,
                self._context,
                self._started_at,
                datetime.now(UTC),
                status,
                self._attributes,
                error_type,
            )
        )


class InMemoryTracing:
    def __init__(self, max_spans: int = 1000) -> None:
        self._max_spans = max_spans
        self._spans: list[SpanRecord] = []
        self._lock = Lock()

    @property
    def ready(self) -> bool:
        return True

    @property
    def spans(self) -> tuple[SpanRecord, ...]:
        with self._lock:
            return tuple(self._spans)

    def start_span(
        self, name: str, context: TraceContext, attributes: Mapping[str, Scalar]
    ) -> _MemorySpan:
        return _MemorySpan(self, name, context, attributes)

    def _record(self, span: SpanRecord) -> None:
        with self._lock:
            self._spans.append(span)
            if len(self._spans) > self._max_spans:
                del self._spans[: len(self._spans) - self._max_spans]


class _DisabledSpan:
    def __init__(self, context: TraceContext) -> None:
        self._context = context

    @property
    def context(self) -> TraceContext:
        return self._context

    def end(self, status: str, error_type: str | None = None) -> None:
        return None


class DisabledTracing:
    @property
    def ready(self) -> bool:
        return True

    def start_span(
        self, name: str, context: TraceContext, attributes: Mapping[str, Scalar]
    ) -> _DisabledSpan:
        return _DisabledSpan(context)


class UnavailableTracing(DisabledTracing):
    @property
    def ready(self) -> bool:
        return False


class _OpenTelemetrySpan:
    def __init__(self, span: OpenTelemetrySpanLike, parent_span_id: str | None) -> None:
        self._span = span
        if not re.fullmatch(r"[0-9a-f]{32}", span.trace_id) or not re.fullmatch(
            r"[0-9a-f]{16}", span.span_id
        ):
            raise ValueError("OpenTelemetry adapter returned invalid trace context")
        self._context = TraceContext(
            span.trace_id,
            span.span_id,
            span.sampled,
            parent_span_id,
        )

    @property
    def context(self) -> TraceContext:
        return self._context

    def end(self, status: str, error_type: str | None = None) -> None:
        try:
            self._span.set_attribute("parkshield.status", status)
            if error_type:
                self._span.set_attribute("error.type", error_type[:80])
            self._span.end()
        except Exception as error:
            log_integration_failure("opentelemetry", "end_span", error)


class OpenTelemetryTracing:
    """Adapter for an injected OpenTelemetry SDK tracer; imports remain optional."""

    def __init__(self, tracer: OpenTelemetryTracerLike) -> None:
        self._tracer = tracer

    @property
    def ready(self) -> bool:
        return True

    def start_span(
        self, name: str, context: TraceContext, attributes: Mapping[str, Scalar]
    ) -> _OpenTelemetrySpan | _DisabledSpan:
        try:
            span = self._tracer.start_span(name, context.parent_traceparent)
            for key, value in attributes.items():
                span.set_attribute(key, value)
            return _OpenTelemetrySpan(span, context.parent_span_id)
        except Exception as error:
            log_integration_failure("opentelemetry", "start_span", error)
            return _DisabledSpan(context)
