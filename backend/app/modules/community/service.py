"""Submission validation and moderation use cases."""

import hashlib
import re
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.modules.community.domain import (
    AppealStatus,
    CommunityReport,
    CommunityReportRepository,
    ReportAppeal,
    ReportCategory,
    ReportStatus,
)


class InvalidReportError(ValueError):
    pass


class DuplicateReportError(ValueError):
    pass


class CommunityReportService:
    def __init__(self, repository: CommunityReportRepository) -> None:
        self._repository = repository

    async def submit(
        self,
        reporter_id: UUID,
        category: ReportCategory,
        latitude: float,
        longitude: float,
        description: str,
        photo: bytes | None = None,
    ) -> CommunityReport:
        cleaned = " ".join(description.split())
        if len(cleaned) < 12:
            raise InvalidReportError("description must contain at least 12 characters")
        if len(cleaned) > 1000 or not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise InvalidReportError("report fields are outside allowed limits")
        normalized = re.sub(r"[^a-z0-9 ]", "", cleaned.casefold())
        material = f"{category}:{latitude:.4f}:{longitude:.4f}:{normalized}"
        fingerprint = hashlib.sha256(material.encode()).hexdigest()
        now = datetime.now(UTC)
        if await self._repository.find_recent_duplicate(fingerprint, now - timedelta(hours=24)):
            raise DuplicateReportError("a matching recent report already exists")
        validation_score = self._validation_score(cleaned, photo)
        status = ReportStatus.PUBLISHED if validation_score >= 0.85 else ReportStatus.PENDING
        report = CommunityReport(
            id=uuid4(),
            reporter_id=reporter_id,
            category=category,
            latitude=latitude,
            longitude=longitude,
            description=cleaned,
            status=status,
            validation_score=validation_score,
            fingerprint=fingerprint,
            photo_sha256=hashlib.sha256(photo).hexdigest() if photo else None,
            created_at=now,
            expires_at=now + timedelta(days=30),
        )
        await self._repository.add(report)
        return report

    async def moderate(
        self, report_id: UUID, approved: bool, reason: str
    ) -> CommunityReport:
        if len(reason.strip()) < 5:
            raise InvalidReportError("a moderation reason is required")
        status = ReportStatus.PUBLISHED if approved else ReportStatus.REJECTED
        report = await self._repository.set_status(report_id, status, reason.strip())
        if report is None:
            raise InvalidReportError("report not found")
        await self._repository.adjust_reputation(report.reporter_id, approved)
        return report

    async def appeal(self, report_id: UUID, appellant_id: UUID, reason: str) -> ReportAppeal:
        report = await self._repository.get(report_id)
        if report is None or report.reporter_id != appellant_id:
            raise InvalidReportError("report not found")
        if report.status is not ReportStatus.REJECTED:
            raise InvalidReportError("only rejected reports can be appealed")
        if len(reason.strip()) < 12:
            raise InvalidReportError("appeal reason must contain at least 12 characters")
        if await self._repository.open_appeal(report_id):
            raise DuplicateReportError("an open appeal already exists")
        appeal = ReportAppeal(
            uuid4(), report_id, appellant_id, reason.strip(), AppealStatus.OPEN, datetime.now(UTC)
        )
        await self._repository.add_appeal(appeal)
        return appeal

    async def resolve_appeal(
        self, appeal_id: UUID, overturned: bool, reason: str
    ) -> ReportAppeal:
        if len(reason.strip()) < 5:
            raise InvalidReportError("a resolution reason is required")
        result = await self._repository.resolve_appeal(
            appeal_id,
            AppealStatus.OVERTURNED if overturned else AppealStatus.UPHELD,
            reason.strip(),
            datetime.now(UTC),
        )
        if result is None:
            raise InvalidReportError("appeal not found")
        if overturned:
            report = await self._repository.set_status(
                result.report_id, ReportStatus.PUBLISHED, "Appeal overturned: " + reason.strip()
            )
            if report:
                await self._repository.adjust_reputation(report.reporter_id, True)
        return result

    @staticmethod
    def _validation_score(description: str, photo: bytes | None) -> float:
        score = 0.45
        if len(description) >= 40:
            score += 0.2
        if photo:
            score += 0.25
        return min(score, 0.95)
