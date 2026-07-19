"""Subscription, store-verification, entitlement, and persistence contracts."""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class StorePlatform(StrEnum):
    APPLE_APP_STORE = "apple_app_store"
    GOOGLE_PLAY = "google_play"


class EntitlementCode(StrEnum):
    PREMIUM = "premium"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    GRACE_PERIOD = "grace_period"
    PAUSED = "paused"
    EXPIRED = "expired"
    REVOKED = "revoked"


class StoreEnvironment(StrEnum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


@dataclass(frozen=True, slots=True)
class BillingProduct:
    platform: StorePlatform
    product_id: str
    entitlement: EntitlementCode


@dataclass(frozen=True, slots=True)
class PurchaseVerificationRequest:
    user_id: UUID
    platform: StorePlatform
    product_id: str
    signed_payload: str


@dataclass(frozen=True, slots=True)
class VerifiedPurchase:
    user_id: UUID
    platform: StorePlatform
    product_id: str
    entitlement: EntitlementCode
    status: SubscriptionStatus
    environment: StoreEnvironment
    provider_event_id: str
    transaction_id: str
    original_transaction_id: str
    purchased_at: datetime
    expires_at: datetime | None
    verified_at: datetime
    auto_renews: bool


@dataclass(frozen=True, slots=True)
class SubscriptionRecord:
    id: UUID
    user_id: UUID | None
    subject_reference: str
    platform: StorePlatform
    product_id: str
    entitlement: EntitlementCode
    status: SubscriptionStatus
    environment: StoreEnvironment
    transaction_reference: str
    original_transaction_reference: str
    purchased_at: datetime
    expires_at: datetime | None
    verified_at: datetime
    auto_renews: bool


@dataclass(frozen=True, slots=True)
class BillingEvent:
    id: UUID
    subscription_id: UUID
    provider_event_reference: str
    status: SubscriptionStatus
    occurred_at: datetime
    received_at: datetime


@dataclass(frozen=True, slots=True)
class EntitlementSnapshot:
    tier: str
    status: str
    platform: StorePlatform | None = None
    product_id: str | None = None
    expires_at: datetime | None = None
    auto_renews: bool = False
    last_verified_at: datetime | None = None


class StorePurchaseVerifier(Protocol):
    @abstractmethod
    async def verify(self, request: PurchaseVerificationRequest) -> VerifiedPurchase:
        """Verify opaque store evidence without trusting client-declared outcomes."""


class BillingRepository(Protocol):
    @abstractmethod
    async def current(self, user_id: UUID) -> SubscriptionRecord | None:
        """Return the newest authoritative record associated with a user."""

    @abstractmethod
    async def reconcile(
        self, subscription: SubscriptionRecord, event: BillingEvent
    ) -> SubscriptionRecord:
        """Idempotently persist verified subscription state and event evidence."""
