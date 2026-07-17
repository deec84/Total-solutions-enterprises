"""Privacy domain entities and ports."""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class ConsentPurpose(StrEnum):
    PRODUCT_ANALYTICS = "product_analytics"
    PERSONALIZED_RECOMMENDATIONS = "personalized_recommendations"
    COMMUNITY_RESEARCH = "community_research"


class DataRequestType(StrEnum):
    EXPORT = "export"
    DELETION = "deletion"


class DataRequestStatus(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class ConsentDecision:
    id: UUID
    user_id: UUID
    purpose: ConsentPurpose
    policy_version: str
    granted: bool
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class DataRightsRequest:
    id: UUID
    user_id: UUID | None
    subject_reference: str
    request_type: DataRequestType
    status: DataRequestStatus
    requested_at: datetime
    completed_at: datetime | None = None


class PrivacyRepository(Protocol):
    @abstractmethod
    async def record_consent(self, decision: ConsentDecision) -> None:
        """Append an immutable optional-consent decision."""

    @abstractmethod
    async def latest_consents(self, user_id: UUID) -> tuple[ConsentDecision, ...]:
        """Return the newest decision for every optional purpose."""

    @abstractmethod
    async def add_request(self, request: DataRightsRequest) -> None:
        """Record a processing data-rights request."""

    @abstractmethod
    async def complete_request(self, request_id: UUID, completed_at: datetime) -> None:
        """Mark a recorded request as completed."""

    @abstractmethod
    async def export_for_user(self, user_id: UUID) -> dict[str, object]:
        """Build a data-minimized, JSON-compatible account snapshot."""

    @abstractmethod
    async def active_media_keys(self, user_id: UUID) -> tuple[str, ...]:
        """Return private media objects that must be deleted with the account."""

    @abstractmethod
    async def delete_account(self, user_id: UUID) -> bool:
        """Remove the user and cascade owned records inside one transaction."""


class PrivateMediaStore(Protocol):
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete one private provider object; implementations must be idempotent."""
