"""Provider-neutral ports for metrics, tracing, and product analytics."""

from abc import abstractmethod
from collections.abc import Mapping
from typing import Protocol

from app.modules.observability.domain import ProductEvent, TraceContext

Scalar = str | int | float | bool


class MetricsPort(Protocol):
    @property
    @abstractmethod
    def ready(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def increment(self, name: str, labels: Mapping[str, str] | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def observe(
        self, name: str, value: float, labels: Mapping[str, str] | None = None
    ) -> None:
        raise NotImplementedError


class SpanPort(Protocol):
    @property
    @abstractmethod
    def context(self) -> TraceContext:
        raise NotImplementedError

    @abstractmethod
    def end(self, status: str, error_type: str | None = None) -> None:
        raise NotImplementedError


class TracingPort(Protocol):
    @property
    @abstractmethod
    def ready(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def start_span(
        self,
        name: str,
        context: TraceContext,
        attributes: Mapping[str, Scalar],
    ) -> SpanPort:
        raise NotImplementedError


class AnalyticsProvider(Protocol):
    @property
    @abstractmethod
    def ready(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def publish(self, event: ProductEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_subject(self, subject_reference: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def purge_expired(self) -> int:
        raise NotImplementedError


class OpenTelemetrySpanLike(Protocol):
    @property
    @abstractmethod
    def trace_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def span_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def sampled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def set_attribute(self, key: str, value: Scalar) -> None:
        raise NotImplementedError

    @abstractmethod
    def end(self) -> None:
        raise NotImplementedError


class OpenTelemetryTracerLike(Protocol):
    """Bridge surface implemented by an environment-owned OpenTelemetry SDK adapter."""

    @abstractmethod
    def start_span(
        self, name: str, parent_traceparent: str | None
    ) -> OpenTelemetrySpanLike:
        raise NotImplementedError
