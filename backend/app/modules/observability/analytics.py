"""Consent-gated, pseudonymous, bounded product analytics."""

import hashlib
import hmac
import json
import logging
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from threading import Lock
from uuid import UUID

from app.modules.observability.domain import MetricName, ProductEvent, ProductEventName
from app.modules.observability.ports import AnalyticsProvider, MetricsPort
from app.modules.observability.redaction import allowlisted_fields, log_integration_failure

EVENT_PROPERTIES: dict[ProductEventName, frozenset[str]] = {
    ProductEventName.SCREEN_VIEWED: frozenset({"screen"}),
    ProductEventName.SESSION_STARTED: frozenset({"platform", "app_version"}),
    ProductEventName.SIGN_IN_COMPLETED: frozenset({"outcome", "mfa_used"}),
    ProductEventName.PARKING_DECISION_VIEWED: frozenset({"risk_band", "source_level"}),
    ProductEventName.PARKING_RECOMMENDATION_OPENED: frozenset(
        {"distance_band", "price_band"}
    ),
    ProductEventName.SIGN_SCAN_COMPLETED: frozenset(
        {"outcome", "source_level", "restriction_count"}
    ),
    ProductEventName.COMMUNITY_REPORT_SUBMITTED: frozenset(
        {"report_type", "outcome"}
    ),
    ProductEventName.TOW_RECOVERY_SEARCHED: frozenset({"outcome", "result_band"}),
    ProductEventName.BILLING_VERIFICATION_COMPLETED: frozenset(
        {"provider", "outcome"}
    ),
}


class InMemoryAnalyticsProvider:
    def __init__(
        self,
        now: Callable[[], datetime] | None = None,
        max_events: int = 10_000,
    ) -> None:
        self._now = now or (lambda: datetime.now(UTC))
        self._max_events = max_events
        self._events: list[ProductEvent] = []
        self._lock = Lock()

    @property
    def ready(self) -> bool:
        return True

    @property
    def events(self) -> tuple[ProductEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def publish(self, event: ProductEvent) -> None:
        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                del self._events[: len(self._events) - self._max_events]

    def delete_subject(self, subject_reference: str) -> int:
        with self._lock:
            previous = len(self._events)
            self._events = [
                event for event in self._events if event.subject_reference != subject_reference
            ]
            return previous - len(self._events)

    def purge_expired(self) -> int:
        now = self._now()
        with self._lock:
            previous = len(self._events)
            self._events = [event for event in self._events if event.expires_at > now]
            return previous - len(self._events)


class DisabledAnalyticsProvider:
    @property
    def ready(self) -> bool:
        return True

    def publish(self, event: ProductEvent) -> None:
        return None

    def delete_subject(self, subject_reference: str) -> int:
        return 0

    def purge_expired(self) -> int:
        return 0


class UnavailableAnalyticsProvider(DisabledAnalyticsProvider):
    @property
    def ready(self) -> bool:
        return False


class ProductAnalytics:
    def __init__(
        self,
        provider: AnalyticsProvider,
        metrics: MetricsPort,
        subject_secret: str,
        retention_days: int,
        enabled: bool,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._provider = provider
        self._metrics = metrics
        self._secret = subject_secret.encode()
        self._retention = timedelta(days=retention_days)
        self._enabled = enabled
        self._now = now or (lambda: datetime.now(UTC))

    @property
    def ready(self) -> bool:
        return self._provider.ready

    @property
    def provider(self) -> AnalyticsProvider:
        return self._provider

    def track(
        self,
        user_id: UUID,
        event_name: ProductEventName,
        properties: Mapping[str, object],
        *,
        consent_granted: bool,
    ) -> bool:
        reason = "disabled" if not self._enabled else "consent"
        if not self._enabled or not consent_granted:
            self._metrics.increment(MetricName.ANALYTICS_REJECTED, {"reason": reason})
            self._log("product_analytics_rejected", reason=reason)
            return False
        cleaned = allowlisted_fields(properties, EVENT_PROPERTIES[event_name])
        if set(properties) != set(cleaned) or any(
            isinstance(value, str) and len(value) > 80 for value in properties.values()
        ):
            self._metrics.increment(MetricName.ANALYTICS_REJECTED, {"reason": "schema"})
            self._log("product_analytics_rejected", reason="schema")
            return False
        occurred_at = self._now()
        try:
            self._provider.publish(
                ProductEvent(
                    event_name,
                    self.subject_reference(user_id),
                    occurred_at,
                    occurred_at + self._retention,
                    cleaned,
                )
            )
        except Exception as error:
            log_integration_failure("product_analytics", "publish", error)
            self._metrics.increment(
                MetricName.ANALYTICS_REJECTED, {"reason": "provider"}
            )
            self._log("product_analytics_rejected", reason="provider")
            return False
        self._metrics.increment(MetricName.ANALYTICS_ACCEPTED, {"event": event_name.value})
        self._log("product_analytics_accepted", event_name=event_name.value)
        return True

    def delete_user(self, user_id: UUID) -> int:
        return self._provider.delete_subject(self.subject_reference(user_id))

    def purge_expired(self) -> int:
        return self._provider.purge_expired()

    def subject_reference(self, user_id: UUID) -> str:
        return hmac.new(self._secret, user_id.bytes, hashlib.sha256).hexdigest()

    @staticmethod
    def _log(event: str, **fields: str) -> None:
        logging.getLogger("parkshield.analytics").info(
            json.dumps(
                {"event": event, **fields},
                separators=(",", ":"),
                sort_keys=True,
            )
        )
