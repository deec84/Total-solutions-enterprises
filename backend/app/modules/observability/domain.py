"""Low-cardinality metrics, trace, and product-event contracts."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class MetricName(StrEnum):
    REQUESTS = "http_requests_total"
    ERRORS = "http_errors_total"
    LATENCY = "http_request_duration_ms"
    AUTHENTICATIONS = "authentications_total"
    MUNICIPAL_IMPORTS = "municipal_imports_total"
    SIGN_ANALYSES = "sign_analyses_total"
    PARKING_SCORE_QUERIES = "parking_score_queries_total"
    COMMUNITY_EVENTS = "community_events_total"
    BILLING_VERIFICATIONS = "billing_verifications_total"
    INTEGRATION_FAILURES = "integration_failures_total"
    ANALYTICS_ACCEPTED = "product_analytics_events_total"
    ANALYTICS_REJECTED = "product_analytics_rejections_total"


class ProductEventName(StrEnum):
    SCREEN_VIEWED = "screen_viewed"
    SESSION_STARTED = "session_started"
    SIGN_IN_COMPLETED = "sign_in_completed"
    PARKING_DECISION_VIEWED = "parking_decision_viewed"
    PARKING_RECOMMENDATION_OPENED = "parking_recommendation_opened"
    SIGN_SCAN_COMPLETED = "sign_scan_completed"
    COMMUNITY_REPORT_SUBMITTED = "community_report_submitted"
    TOW_RECOVERY_SEARCHED = "tow_recovery_searched"
    BILLING_VERIFICATION_COMPLETED = "billing_verification_completed"


@dataclass(frozen=True, slots=True)
class TraceContext:
    trace_id: str
    span_id: str
    sampled: bool
    parent_span_id: str | None = None

    @property
    def traceparent(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-{'01' if self.sampled else '00'}"

    @property
    def parent_traceparent(self) -> str | None:
        if self.parent_span_id is None:
            return None
        return (
            f"00-{self.trace_id}-{self.parent_span_id}-"
            f"{'01' if self.sampled else '00'}"
        )


@dataclass(frozen=True, slots=True)
class SpanRecord:
    name: str
    context: TraceContext
    started_at: datetime
    ended_at: datetime
    status: str
    attributes: Mapping[str, str | int | float | bool]
    error_type: str | None = None


@dataclass(frozen=True, slots=True)
class ProductEvent:
    name: ProductEventName
    subject_reference: str
    occurred_at: datetime
    expires_at: datetime
    properties: Mapping[str, str | int | float | bool]
