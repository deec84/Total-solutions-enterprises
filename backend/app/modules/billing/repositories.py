"""Concurrency-safe in-memory billing adapter for isolated tests."""

import asyncio
from uuid import UUID

from app.modules.billing.domain import BillingEvent, SubscriptionRecord


class InMemoryBillingRepository:
    def __init__(self) -> None:
        self._subscriptions: dict[UUID, SubscriptionRecord] = {}
        self._events: dict[str, BillingEvent] = {}
        self._lock = asyncio.Lock()

    async def current(self, user_id: UUID) -> SubscriptionRecord | None:
        matches = [item for item in self._subscriptions.values() if item.user_id == user_id]
        return max(matches, key=lambda item: item.verified_at, default=None)

    async def reconcile(
        self, subscription: SubscriptionRecord, event: BillingEvent
    ) -> SubscriptionRecord:
        async with self._lock:
            existing_event = self._events.get(event.provider_event_reference)
            existing = next(
                (
                    item
                    for item in self._subscriptions.values()
                    if item.platform is subscription.platform
                    and item.environment is subscription.environment
                    and item.original_transaction_reference
                    == subscription.original_transaction_reference
                ),
                None,
            )
            if existing_event is not None and existing is not None:
                return existing
            if existing is not None and existing.verified_at > subscription.verified_at:
                self._events[event.provider_event_reference] = event
                return existing
            if existing is not None:
                self._subscriptions.pop(existing.id, None)
            self._subscriptions[subscription.id] = subscription
            self._events[event.provider_event_reference] = event
            return subscription

    def events(self) -> tuple[BillingEvent, ...]:
        return tuple(self._events.values())
