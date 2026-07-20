"""Observability, privacy filtering, and provider contract tests."""

import json
import logging
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.infrastructure.database import database_session
from app.main import create_app
from app.modules.identity.domain import Role, User
from app.modules.observability.analytics import (
    DisabledAnalyticsProvider,
    InMemoryAnalyticsProvider,
    ProductAnalytics,
    UnavailableAnalyticsProvider,
)
from app.modules.observability.domain import MetricName, ProductEvent, ProductEventName
from app.modules.observability.metrics import DisabledMetrics, InMemoryMetrics
from app.modules.observability.ports import Scalar
from app.modules.observability.redaction import allowlisted_fields, log_integration_failure
from app.modules.observability.runtime import RequestObservation, build_observability_runtime
from app.modules.observability.schemas import ProductEventCommand
from app.modules.observability.tracing import (
    DisabledTracing,
    InMemoryTracing,
    OpenTelemetryTracing,
    trace_context,
)
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.health import check_database
from app.shared.config import Settings


def test_w3c_trace_context_continues_valid_trace_and_rejects_invalid_parent() -> None:
    parent = f"00-{'1' * 32}-{'2' * 16}-01"
    continued = trace_context(parent)
    replaced = trace_context(f"00-{'0' * 32}-{'0' * 16}-00")

    assert continued.trace_id == "1" * 32
    assert continued.span_id != "2" * 16
    assert continued.sampled is True
    assert continued.traceparent.endswith("-01")
    assert replaced.trace_id != "0" * 32
    assert len(replaced.trace_id) == 32


def test_memory_metrics_and_tracing_are_bounded_and_idempotent() -> None:
    metrics = InMemoryMetrics()
    metrics.increment("requests", {"route": "health"})
    metrics.observe("latency", 12.5, {"route": "health"})
    snapshot = metrics.snapshot()

    tracing = InMemoryTracing(max_spans=1)
    first = tracing.start_span("first", trace_context(None), {"safe": True})
    first.end("ok")
    first.end("error")
    second = tracing.start_span("second", trace_context(None), {})
    second.end("error", "TimeoutError")

    assert metrics.ready is True
    assert next(iter(snapshot.counters.values())) == 1
    assert next(iter(snapshot.observations.values())) == (12.5,)
    assert len(tracing.spans) == 1
    assert tracing.spans[0].name == "second"
    assert tracing.spans[0].error_type == "TimeoutError"


class FakeOtelSpan:
    def __init__(self) -> None:
        self.trace_id = "c" * 32
        self.span_id = "d" * 16
        self.sampled = True
        self.attributes: dict[str, Scalar] = {}
        self.ended = False

    def set_attribute(self, key: str, value: Scalar) -> None:
        self.attributes[key] = value

    def end(self) -> None:
        self.ended = True


class FakeOtelTracer:
    def __init__(self) -> None:
        self.span = FakeOtelSpan()
        self.parent_traceparent: str | None = None

    def start_span(
        self, name: str, parent_traceparent: str | None
    ) -> FakeOtelSpan:
        self.parent_traceparent = parent_traceparent
        self.span.attributes["span.name"] = name
        return self.span


class FailingOtelTracer:
    def start_span(
        self, name: str, parent_traceparent: str | None
    ) -> FakeOtelSpan:
        raise RuntimeError("authorization=must-not-be-logged")


class FailingAnalyticsProvider:
    @property
    def ready(self) -> bool:
        return True

    def publish(self, event: ProductEvent) -> None:
        raise RuntimeError("receipt=must-not-be-logged")

    def delete_subject(self, subject_reference: str) -> int:
        raise RuntimeError("deletion unavailable")

    def purge_expired(self) -> int:
        raise RuntimeError("purge unavailable")


def test_opentelemetry_adapter_uses_only_injected_sdk_surface() -> None:
    tracer = FakeOtelTracer()
    adapter = OpenTelemetryTracing(tracer)
    parent = trace_context(f"00-{'a' * 32}-{'b' * 16}-01")
    span = adapter.start_span("operation", parent, {"safe": "value"})
    span.end("error", "GatewayUnavailable")

    assert adapter.ready is True
    assert tracer.span.ended is True
    assert tracer.span.attributes["safe"] == "value"
    assert tracer.span.attributes["error.type"] == "GatewayUnavailable"
    assert tracer.parent_traceparent == f"00-{'a' * 32}-{'b' * 16}-01"
    assert span.context.trace_id == "c" * 32


def test_opentelemetry_adapter_failure_does_not_break_request_or_leak(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="parkshield.integrations")
    context = trace_context(None)
    span = OpenTelemetryTracing(FailingOtelTracer()).start_span(
        "operation", context, {}
    )
    span.end("ok")

    assert span.context == context
    assert "must-not-be-logged" not in caplog.records[-1].message


def test_product_analytics_requires_consent_and_exact_allowlist() -> None:
    metrics = InMemoryMetrics()
    provider = InMemoryAnalyticsProvider()
    analytics = ProductAnalytics(provider, metrics, "s" * 40, 30, True)
    subject = uuid4()

    assert not analytics.track(
        subject,
        ProductEventName.SIGN_IN_COMPLETED,
        {"outcome": "success"},
        consent_granted=False,
    )
    assert not analytics.track(
        subject,
        ProductEventName.SIGN_IN_COMPLETED,
        {"outcome": "success", "email": "person@example.test"},
        consent_granted=True,
    )
    assert not analytics.track(
        subject,
        ProductEventName.SIGN_IN_COMPLETED,
        {"outcome": "x" * 81},
        consent_granted=True,
    )
    assert analytics.track(
        subject,
        ProductEventName.SIGN_IN_COMPLETED,
        {"outcome": "success", "mfa_used": True},
        consent_granted=True,
    )

    assert len(provider.events) == 1
    assert provider.events[0].subject_reference != str(subject)
    assert len(provider.events[0].subject_reference) == 64
    assert provider.events[0].properties == {"outcome": "success", "mfa_used": True}
    assert analytics.delete_user(subject) == 1


def test_product_analytics_retention_purge_and_memory_bound() -> None:
    current = datetime(2026, 7, 19, tzinfo=UTC)

    def clock() -> datetime:
        return current

    provider = InMemoryAnalyticsProvider(clock, max_events=1)
    analytics = ProductAnalytics(provider, DisabledMetrics(), "s" * 40, 1, True, clock)

    for _ in range(2):
        assert analytics.track(
            uuid4(),
            ProductEventName.SESSION_STARTED,
            {"platform": "ios"},
            consent_granted=True,
        )
    assert len(provider.events) == 1
    current += timedelta(days=2)
    assert analytics.purge_expired() == 1
    assert provider.events == ()


def test_product_analytics_provider_failure_is_rejected_without_payload_leak(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="parkshield.integrations")
    analytics = ProductAnalytics(
        FailingAnalyticsProvider(), InMemoryMetrics(), "s" * 40, 30, True
    )
    accepted = analytics.track(
        uuid4(),
        ProductEventName.BILLING_VERIFICATION_COMPLETED,
        {"provider": "apple", "outcome": "verified"},
        consent_granted=True,
    )

    assert accepted is False
    assert "must-not-be-logged" not in caplog.records[-1].message


def test_disabled_and_unavailable_providers_fail_safely() -> None:
    event_provider = DisabledAnalyticsProvider()
    unavailable = UnavailableAnalyticsProvider()
    disabled_metrics = DisabledMetrics()
    disabled_tracing = DisabledTracing()
    disabled_tracing.start_span("noop", trace_context(None), {}).end("ok")

    assert event_provider.ready is True
    assert event_provider.delete_subject("subject") == 0
    assert event_provider.purge_expired() == 0
    assert unavailable.ready is False
    assert disabled_metrics.ready is True
    disabled_metrics.increment("ignored")
    disabled_metrics.observe("ignored", 1)


def test_allowlist_and_failure_log_drop_sensitive_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    cleaned = allowlisted_fields(
        {"outcome": "ok", "token": "secret", "nested": {"bad": True}},
        frozenset({"outcome", "token", "nested"}),
    )
    caplog.set_level(logging.WARNING, logger="parkshield.integrations")
    log_integration_failure(
        "synthetic_provider", "verify", RuntimeError("token=must-not-appear")
    )
    payload = json.loads(caplog.records[-1].message)

    assert cleaned == {"outcome": "ok"}
    assert payload["error_type"] == "RuntimeError"
    assert "must-not-appear" not in caplog.records[-1].message


def test_runtime_records_required_request_metrics() -> None:
    runtime = build_observability_runtime(Settings(environment="test"))
    runtime.observe_request(RequestObservation("POST", "authentication", 503, 42.0))
    runtime.integration_failure("synthetic")
    assert isinstance(runtime.metrics, InMemoryMetrics)
    snapshot = runtime.metrics.snapshot()
    names = {key[0] for key in snapshot.counters}

    assert runtime.ready is True
    assert MetricName.REQUESTS in names
    assert MetricName.ERRORS in names
    assert MetricName.AUTHENTICATIONS in names
    assert MetricName.INTEGRATION_FAILURES in names
    assert MetricName.LATENCY in {key[0] for key in snapshot.observations}


def test_uninjected_external_providers_fail_readiness() -> None:
    runtime = build_observability_runtime(
        Settings(
            environment="test",
            observability_provider="opentelemetry",
            product_analytics_provider="external",
        )
    )
    assert runtime.ready is False


def test_injected_monitoring_adapters_satisfy_readiness_contract() -> None:
    runtime = build_observability_runtime(
        Settings(
            environment="test",
            observability_provider="opentelemetry",
            product_analytics_provider="external",
        ),
        otel_tracer=FakeOtelTracer(),
        analytics_provider=InMemoryAnalyticsProvider(),
    )

    assert runtime.ready is True
    span = runtime.start_request_span(trace_context(None), {"safe": True})
    span.end("ok")


def test_request_middleware_propagates_safe_context_and_records_metrics() -> None:
    application = create_app()
    with TestClient(application) as client:
        response = client.get(
            "/api/v1/health/live",
            headers={
                "X-Request-ID": "request-19",
                "X-Correlation-ID": "correlation-19",
                "traceparent": f"00-{'a' * 32}-{'b' * 16}-01",
            },
        )

    runtime = application.state.observability
    assert response.headers["X-Request-ID"] == "request-19"
    assert response.headers["X-Correlation-ID"] == "correlation-19"
    assert response.headers["traceparent"].startswith(f"00-{'a' * 32}-")
    assert isinstance(runtime.metrics, InMemoryMetrics)
    assert MetricName.REQUESTS in {key[0] for key in runtime.metrics.snapshot().counters}


def test_readiness_fails_when_configured_exporter_is_unavailable() -> None:
    application = create_app(
        build_observability_runtime(
            Settings(environment="test", observability_provider="opentelemetry")
        )
    )
    application.dependency_overrides[check_database] = lambda: None
    with TestClient(application) as client:
        response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "observability provider unavailable"


def test_product_event_schema_rejects_sensitive_and_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="prohibited field"):
        ProductEventCommand(
            name=ProductEventName.SESSION_STARTED,
            properties={"access_token": "not-allowed"},
        )
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ProductEventCommand.model_validate(
            {"name": "session_started", "properties": {}, "user_id": str(uuid4())}
        )


def test_analytics_api_honors_latest_product_consent() -> None:
    subject = User(
        uuid4(),
        "analytics@example.test",
        "hash",
        Role.USER,
        True,
        True,
        datetime.now(UTC),
    )
    consent_row = SimpleNamespace(
        id=uuid4(),
        user_id=subject.id,
        purpose="product_analytics",
        policy_version="policy-v1",
        granted=True,
        occurred_at=datetime.now(UTC),
    )
    session = AsyncMock()
    session.scalars.return_value = (consent_row,)

    async def fake_session():
        yield session

    settings = Settings(
        environment="test",
        product_analytics_enabled=True,
        product_analytics_provider="memory",
        product_analytics_subject_secret="a" * 40,
    )
    application = create_app(build_observability_runtime(settings))
    application.dependency_overrides[current_user] = lambda: subject
    application.dependency_overrides[database_session] = fake_session
    with TestClient(application) as client:
        accepted = client.post(
            "/api/v1/analytics/events",
            json={
                "name": "parking_decision_viewed",
                "properties": {"risk_band": "safe", "source_level": "official"},
            },
        )
    provider = application.state.observability.analytics.provider

    assert accepted.status_code == 202
    assert accepted.json() == {"accepted": True}
    assert isinstance(provider, InMemoryAnalyticsProvider)
    assert len(provider.events) == 1
