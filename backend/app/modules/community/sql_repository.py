"""PostgreSQL community-report repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import (
    CommunityReportRow,
    ReportAppealRow,
    ReporterReputationRow,
)
from app.modules.community.domain import (
    AppealStatus,
    CommunityReport,
    ReportAppeal,
    ReportCategory,
    ReporterReputation,
    ReportStatus,
)


def _domain(row: CommunityReportRow) -> CommunityReport:
    return CommunityReport(
        id=row.id,
        reporter_id=row.reporter_id,
        category=ReportCategory(row.category),
        latitude=row.latitude,
        longitude=row.longitude,
        description=row.description,
        status=ReportStatus(row.status),
        validation_score=row.validation_score,
        fingerprint=row.fingerprint,
        photo_sha256=row.photo_sha256,
        created_at=row.created_at,
        expires_at=row.expires_at,
        moderation_reason=row.moderation_reason,
    )


def _appeal(row: ReportAppealRow) -> ReportAppeal:
    return ReportAppeal(
        row.id,
        row.report_id,
        row.appellant_id,
        row.reason,
        AppealStatus(row.status),
        row.created_at,
        row.resolved_at,
        row.resolution_reason,
    )


class SqlCommunityReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, report: CommunityReport) -> None:
        self._session.add(
            CommunityReportRow(
                id=report.id,
                reporter_id=report.reporter_id,
                category=report.category,
                latitude=report.latitude,
                longitude=report.longitude,
                description=report.description,
                status=report.status,
                validation_score=report.validation_score,
                fingerprint=report.fingerprint,
                photo_sha256=report.photo_sha256,
                moderation_reason=report.moderation_reason,
                created_at=report.created_at,
                expires_at=report.expires_at,
            )
        )
        await self._session.flush()

    async def find_recent_duplicate(
        self, fingerprint: str, since: datetime
    ) -> CommunityReport | None:
        row = await self._session.scalar(
            select(CommunityReportRow).where(
                CommunityReportRow.fingerprint == fingerprint,
                CommunityReportRow.created_at >= since,
            )
        )
        return _domain(row) if row else None

    async def pending(self, limit: int) -> tuple[CommunityReport, ...]:
        rows = await self._session.scalars(
            select(CommunityReportRow)
            .where(CommunityReportRow.status == ReportStatus.PENDING)
            .order_by(CommunityReportRow.created_at)
            .limit(limit)
        )
        return tuple(_domain(row) for row in rows)

    async def get(self, report_id: UUID) -> CommunityReport | None:
        row = await self._session.get(CommunityReportRow, report_id)
        return _domain(row) if row else None

    async def set_status(
        self, report_id: UUID, status: ReportStatus, reason: str
    ) -> CommunityReport | None:
        await self._session.execute(
            update(CommunityReportRow)
            .where(CommunityReportRow.id == report_id)
            .values(status=status, moderation_reason=reason)
        )
        return await self.get(report_id)

    async def adjust_reputation(self, user_id: UUID, approved: bool) -> ReporterReputation:
        statement = insert(ReporterReputationRow).values(
            user_id=user_id,
            score=0.55 if approved else 0.4,
            approved_reports=int(approved),
            rejected_reports=int(not approved),
        )
        statement = statement.on_conflict_do_update(
            index_elements=[ReporterReputationRow.user_id],
            set_={
                "score": (
                    ReporterReputationRow.score + (0.05 if approved else -0.1)
                ),
                "approved_reports": ReporterReputationRow.approved_reports + int(approved),
                "rejected_reports": ReporterReputationRow.rejected_reports + int(not approved),
            },
        )
        await self._session.execute(statement)
        return await self.reputation(user_id)

    async def reputation(self, user_id: UUID) -> ReporterReputation:
        row = await self._session.get(ReporterReputationRow, user_id)
        if row is None:
            return ReporterReputation(user_id, 0.5, 0, 0)
        return ReporterReputation(
            row.user_id, row.score, row.approved_reports, row.rejected_reports
        )

    async def add_appeal(self, appeal: ReportAppeal) -> None:
        self._session.add(
            ReportAppealRow(
                id=appeal.id,
                report_id=appeal.report_id,
                appellant_id=appeal.appellant_id,
                reason=appeal.reason,
                status=appeal.status,
                created_at=appeal.created_at,
                resolved_at=appeal.resolved_at,
                resolution_reason=appeal.resolution_reason,
            )
        )
        await self._session.flush()

    async def open_appeal(self, report_id: UUID) -> ReportAppeal | None:
        row = await self._session.scalar(
            select(ReportAppealRow).where(
                ReportAppealRow.report_id == report_id,
                ReportAppealRow.status == AppealStatus.OPEN,
            )
        )
        return _appeal(row) if row else None

    async def resolve_appeal(
        self, appeal_id: UUID, status: AppealStatus, reason: str, resolved_at: datetime
    ) -> ReportAppeal | None:
        await self._session.execute(
            update(ReportAppealRow)
            .where(ReportAppealRow.id == appeal_id)
            .values(status=status, resolution_reason=reason, resolved_at=resolved_at)
        )
        row = await self._session.get(ReportAppealRow, appeal_id)
        return _appeal(row) if row else None
