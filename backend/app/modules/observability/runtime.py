"""Per-application composition root for local and future external telemetry."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.modules.observability.analytics import (
    DisabledAnalyticsProvider,
    InMemoryAnalyticsProvider,
    ProductAnalytics,
    UnavailableAnalyticsProvider,
)
from app.modules.observability.domain import MetricName, TraceContext
from app.modules.observability.metrics import DisabledMetrics, InMemoryMetrics, UnavailableMetrics
from app.modules.observability.ports import (
    AnalyticsProvider,
    MetricsPort,
    OpenTelemetryTracerLike,
    Scalar,
    SpanPort,
    TracingPort,
)
from app.modules.observability.tracing import (
    DisabledTracing,
    InMemoryTracing,
    OpenTelemetryTracing,
    UnavailableTracing,
)

if TYPE_CHECKING:
    from app.shared.config import Settings

_CATEGORY_METRICS: dict[str, MetricName] = {
    "authentication": MetricName.AUTHENTICATIONS,
    "municipal_import": MetricName.MUNICIPAL_IMPORTS,
    "sign_analysis": MetricName.SIGN_ANALYSES,
    "parking_score": MetricName.PARKING_SCORE_QUERIES,
    "community": MetricName.COMMUNITY_EVENTS,
    "billing": MetricName.BILLING_VERIFICATIONS,
}


@dataclass(frozen=True, slots=True)
class RequestObservation:
    method: str
    category: str
    status_code: int
    duration_ms: float


class ObservabilityRuntime:
    def __init__(
        self,
        metrics: MetricsPort,
        tracing: TracingPort,
        analytics: ProductAnalytics,
        service_name: str,
    ) -> None:
        self.metrics = metrics
        self.tracing = tracing
        self.analytics = analytics
        self.service_name = service_name

    @property
    def ready(self) -> bool:
        return self.metrics.ready and self.tracing.ready and self.analytics.ready

    def observe_request(self, observation: RequestObservation) -> None:
        outcome = f"{observation.status_code // 100}xx"
        labels = {
            "category": observation.category,
            "method": observation.method,
            "outcome": outcome,
        }
        self.metrics.increment(MetricName.REQUESTS, labels)
        self.metrics.observe(MetricName.LATENCY, observation.duration_ms, labels)
        if observation.status_code >= 500:
            self.metrics.increment(MetricName.ERRORS, labels)
        metric = _CATEGORY_METRICS.get(observation.category)
        if metric is not None:
            self.metrics.increment(metric, {"outcome": outcome})

    def start_request_span(
        self, context: TraceContext, attributes: Mapping[str, Scalar]
    ) -> SpanPort:
        return self.tracing.start_span(
            "http.server.request",
            context,
            {"service.name": self.service_name, **attributes},
        )

    def integration_failure(self, provider: str) -> None:
        self.metrics.increment(
            MetricName.INTEGRATION_FAILURES, {"provider": provider[:40]}
        )


def build_observability_runtime(
    settings: "Settings",
    *,
    otel_tracer: OpenTelemetryTracerLike | None = None,
    analytics_provider: AnalyticsProvider | None = None,
) -> ObservabilityRuntime:
    metrics: MetricsPort
    tracing: TracingPort
    if settings.observability_provider == "memory":
        metrics = InMemoryMetrics()
        tracing = InMemoryTracing()
    elif settings.observability_provider == "disabled":
        metrics = DisabledMetrics()
        tracing = DisabledTracing()
    elif otel_tracer is None:
        metrics = UnavailableMetrics()
        tracing = UnavailableTracing()
    else:
        metrics = InMemoryMetrics()
        tracing = OpenTelemetryTracing(otel_tracer)

    if analytics_provider is not None:
        provider = analytics_provider
    elif settings.product_analytics_provider == "memory":
        provider = InMemoryAnalyticsProvider()
    elif settings.product_analytics_provider == "external":
        provider = UnavailableAnalyticsProvider()
    else:
        provider = DisabledAnalyticsProvider()

    analytics = ProductAnalytics(
        provider,
        metrics,
        settings.product_analytics_subject_secret,
        settings.product_analytics_retention_days,
        settings.product_analytics_enabled,
    )
    return ObservabilityRuntime(
        metrics, tracing, analytics, settings.observability_service_name
    )
