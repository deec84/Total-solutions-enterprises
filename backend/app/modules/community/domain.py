"""Community report domain and persistence port."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class ReportCategory(StrEnum):
    TOWING = "towing"
    RESTRICTION = "restriction"
    PRICE = "price"
    SIGN = "sign"


class ReportStatus(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    REJECTED = "rejected"


class AppealStatus(StrEnum):
    OPEN = "open"
    UPHELD = "upheld"
    OVERTURNED = "overturned"


@dataclass(frozen=True, slots=True)
class CommunityReport:
    id: UUID
    reporter_id: UUID
    category: ReportCategory
    latitude: float
    longitude: float
    description: str
    status: ReportStatus
    validation_score: float
    fingerprint: str
    photo_sha256: str | None
    created_at: datetime
    expires_at: datetime
    moderation_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ReportAppeal:
    id: UUID
    report_id: UUID
    appellant_id: UUID
    reason: str
    status: AppealStatus
    created_at: datetime
    resolved_at: datetime | None = None
    resolution_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ReporterReputation:
    user_id: UUID
    score: float
    approved_reports: int
    rejected_reports: int


class CommunityReportRepository(Protocol):
    async def add(self, report: CommunityReport) -> None: ...
    async def find_recent_duplicate(
        self, fingerprint: str, since: datetime
    ) -> CommunityReport | None: ...
    async def pending(self, limit: int) -> tuple[CommunityReport, ...]: ...
    async def get(self, report_id: UUID) -> CommunityReport | None: ...
    async def set_status(
        self, report_id: UUID, status: ReportStatus, reason: str
    ) -> CommunityReport | None: ...
    async def adjust_reputation(self, user_id: UUID, approved: bool) -> ReporterReputation: ...
    async def reputation(self, user_id: UUID) -> ReporterReputation: ...
    async def add_appeal(self, appeal: ReportAppeal) -> None: ...
    async def open_appeal(self, report_id: UUID) -> ReportAppeal | None: ...
    async def resolve_appeal(
        self, appeal_id: UUID, status: AppealStatus, reason: str, resolved_at: datetime
    ) -> ReportAppeal | None: ...
