"""Provider-neutral ports for metrics, tracing, and product analytics."""

from collections.abc import Mapping
from typing import Protocol

from app.modules.observability.domain import ProductEvent, SpanRecord, TraceContext

Scalar = str | int | float | bool


class MetricsPort(Protocol):
    @property
    def ready(self) -> bool: ...

    def increment(self, name: str, labels: Mapping[str, str] | None = None) -> None: ...

    def observe(
        self, name: str, value: float, labels: Mapping[str, str] | None = None
    ) -> None: ...


class SpanPort(Protocol):
    @property
    def context(self) -> TraceContext: ...

    def end(self, status: str, error_type: str | None = None) -> None: ...


class TracingPort(Protocol):
    @property
    def ready(self) -> bool: ...

    def start_span(
        self,
        name: str,
        context: TraceContext,
        attributes: Mapping[str, Scalar],
    ) -> SpanPort: ...


class AnalyticsProvider(Protocol):
    @property
    def ready(self) -> bool: ...

    def publish(self, event: ProductEvent) -> None: ...

    def delete_subject(self, subject_reference: str) -> int: ...

    def purge_expired(self) -> int: ...


class OpenTelemetrySpanLike(Protocol):
    @property
    def trace_id(self) -> str: ...

    @property
    def span_id(self) -> str: ...

    @property
    def sampled(self) -> bool: ...

    def set_attribute(self, key: str, value: Scalar) -> None: ...

    def end(self) -> None: ...


class OpenTelemetryTracerLike(Protocol):
    """Bridge surface implemented by an environment-owned OpenTelemetry SDK adapter."""

    def start_span(
        self, name: str, parent_traceparent: str | None
    ) -> OpenTelemetrySpanLike: ...


class TraceRecorder(Protocol):
    @property
    def spans(self) -> tuple[SpanRecord, ...]: ...
