"""Isolated in-memory repository used by unit tests."""

from dataclasses import replace
from datetime import datetime
from uuid import UUID

from app.modules.community.domain import (
    AppealStatus,
    CommunityReport,
    ReportAppeal,
    ReporterReputation,
    ReportStatus,
)


class InMemoryCommunityReportRepository:
    def __init__(self) -> None:
        self._reports: dict[UUID, CommunityReport] = {}
        self._reputations: dict[UUID, ReporterReputation] = {}
        self._appeals: dict[UUID, ReportAppeal] = {}

    async def add(self, report: CommunityReport) -> None:
        self._reports[report.id] = report

    async def find_recent_duplicate(
        self, fingerprint: str, since: datetime
    ) -> CommunityReport | None:
        return next(
            (
                report
                for report in self._reports.values()
                if report.fingerprint == fingerprint and report.created_at >= since
            ),
            None,
        )

    async def pending(self, limit: int) -> tuple[CommunityReport, ...]:
        reports = (r for r in self._reports.values() if r.status is ReportStatus.PENDING)
        return tuple(sorted(reports, key=lambda r: r.created_at)[:limit])

    async def get(self, report_id: UUID) -> CommunityReport | None:
        return self._reports.get(report_id)

    async def set_status(
        self, report_id: UUID, status: ReportStatus, reason: str
    ) -> CommunityReport | None:
        report = self._reports.get(report_id)
        if report is None:
            return None
        updated = replace(report, status=status, moderation_reason=reason)
        self._reports[report_id] = updated
        return updated

    async def adjust_reputation(self, user_id: UUID, approved: bool) -> ReporterReputation:
        current = await self.reputation(user_id)
        updated = ReporterReputation(
            user_id,
            min(1.0, current.score + 0.05) if approved else max(0.0, current.score - 0.1),
            current.approved_reports + int(approved),
            current.rejected_reports + int(not approved),
        )
        self._reputations[user_id] = updated
        return updated

    async def reputation(self, user_id: UUID) -> ReporterReputation:
        return self._reputations.get(user_id, ReporterReputation(user_id, 0.5, 0, 0))

    async def add_appeal(self, appeal: ReportAppeal) -> None:
        self._appeals[appeal.id] = appeal

    async def open_appeal(self, report_id: UUID) -> ReportAppeal | None:
        return next(
            (
                appeal
                for appeal in self._appeals.values()
                if appeal.report_id == report_id and appeal.status is AppealStatus.OPEN
            ),
            None,
        )

    async def resolve_appeal(
        self, appeal_id: UUID, status: AppealStatus, reason: str, resolved_at: datetime
    ) -> ReportAppeal | None:
        appeal = self._appeals.get(appeal_id)
        if appeal is None:
            return None
        updated = replace(
            appeal, status=status, resolution_reason=reason, resolved_at=resolved_at
        )
        self._appeals[appeal_id] = updated
        return updated
