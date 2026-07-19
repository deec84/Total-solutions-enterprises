"""PostgreSQL privacy repository with data-minimized export mapping."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import (
    AlertDeliveryRow,
    AuditEventRow,
    CommunityReportRow,
    DataRightsRequestRow,
    NotificationPreferenceRow,
    PrivacyConsentEventRow,
    PushDeviceRow,
    ReportAppealRow,
    ReporterReputationRow,
    SessionRow,
    UserRow,
)
from app.modules.privacy.domain import (
    ConsentDecision,
    ConsentPurpose,
    DataRequestStatus,
    DataRightsRequest,
)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _consent(row: PrivacyConsentEventRow) -> ConsentDecision:
    return ConsentDecision(
        row.id,
        row.user_id,
        ConsentPurpose(row.purpose),
        row.policy_version,
        row.granted,
        row.occurred_at,
    )


class SqlPrivacyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_consent(self, decision: ConsentDecision) -> None:
        self._session.add(
            PrivacyConsentEventRow(
                id=decision.id,
                user_id=decision.user_id,
                purpose=decision.purpose.value,
                policy_version=decision.policy_version,
                granted=decision.granted,
                occurred_at=decision.occurred_at,
            )
        )
        await self._session.flush()

    async def latest_consents(self, user_id: UUID) -> tuple[ConsentDecision, ...]:
        rows = await self._session.scalars(
            select(PrivacyConsentEventRow)
            .where(PrivacyConsentEventRow.user_id == user_id)
            .order_by(
                PrivacyConsentEventRow.purpose,
                PrivacyConsentEventRow.occurred_at.desc(),
                PrivacyConsentEventRow.id.desc(),
            )
        )
        latest: dict[str, ConsentDecision] = {}
        for row in rows:
            latest.setdefault(row.purpose, _consent(row))
        return tuple(latest[purpose] for purpose in sorted(latest))

    async def add_request(self, request: DataRightsRequest) -> None:
        self._session.add(
            DataRightsRequestRow(
                id=request.id,
                user_id=request.user_id,
                subject_reference=request.subject_reference,
                request_type=request.request_type.value,
                status=request.status.value,
                requested_at=request.requested_at,
                completed_at=request.completed_at,
            )
        )
        await self._session.flush()

    async def complete_request(self, request_id: UUID, completed_at: datetime) -> None:
        await self._session.execute(
            update(DataRightsRequestRow)
            .where(
                DataRightsRequestRow.id == request_id,
                DataRightsRequestRow.status == DataRequestStatus.PROCESSING.value,
            )
            .values(
                status=DataRequestStatus.COMPLETED.value,
                completed_at=completed_at,
            )
        )

    async def export_for_user(self, user_id: UUID) -> dict[str, object]:
        user = await self._session.get(UserRow, user_id)
        if user is None:
            raise ValueError("account no longer exists")
        sessions = tuple(
            await self._session.scalars(
                select(SessionRow)
                .where(SessionRow.user_id == user_id)
                .order_by(SessionRow.created_at)
            )
        )
        reports = tuple(
            await self._session.scalars(
                select(CommunityReportRow)
                .where(CommunityReportRow.reporter_id == user_id)
                .order_by(CommunityReportRow.created_at)
            )
        )
        appeals = tuple(
            await self._session.scalars(
                select(ReportAppealRow)
                .where(ReportAppealRow.appellant_id == user_id)
                .order_by(ReportAppealRow.created_at)
            )
        )
        consent_events = tuple(
            await self._session.scalars(
                select(PrivacyConsentEventRow)
                .where(PrivacyConsentEventRow.user_id == user_id)
                .order_by(PrivacyConsentEventRow.occurred_at)
            )
        )
        requests = tuple(
            await self._session.scalars(
                select(DataRightsRequestRow)
                .where(DataRightsRequestRow.user_id == user_id)
                .order_by(DataRightsRequestRow.requested_at)
            )
        )
        devices = tuple(
            await self._session.scalars(
                select(PushDeviceRow)
                .where(PushDeviceRow.user_id == user_id)
                .order_by(PushDeviceRow.updated_at)
            )
        )
        deliveries = tuple(
            await self._session.scalars(
                select(AlertDeliveryRow)
                .where(AlertDeliveryRow.user_id == user_id)
                .order_by(AlertDeliveryRow.created_at)
            )
        )
        preferences = await self._session.get(NotificationPreferenceRow, user_id)
        reputation = await self._session.get(ReporterReputationRow, user_id)
        audit_events = tuple(
            await self._session.scalars(
                select(AuditEventRow)
                .where(AuditEventRow.subject_id == user_id)
                .order_by(AuditEventRow.occurred_at)
            )
        )
        return {
            "profile": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "mfa_enabled": user.mfa_enabled,
                "created_at": _iso(user.created_at),
            },
            "sessions": [
                {
                    "id": str(item.id),
                    "created_at": _iso(item.created_at),
                    "expires_at": _iso(item.expires_at),
                }
                for item in sessions
            ],
            "community_reports": [
                {
                    "id": str(item.id),
                    "category": item.category,
                    "latitude": item.latitude,
                    "longitude": item.longitude,
                    "description": item.description,
                    "status": item.status,
                    "validation_score": item.validation_score,
                    "photo_sha256": item.photo_sha256,
                    "photo_content_type": item.photo_content_type,
                    "photo_size_bytes": item.photo_size_bytes,
                    "photo_retained_until": _iso(item.photo_retained_until),
                    "photo_deleted_at": _iso(item.photo_deleted_at),
                    "moderation_reason": item.moderation_reason,
                    "created_at": _iso(item.created_at),
                    "expires_at": _iso(item.expires_at),
                }
                for item in reports
            ],
            "report_appeals": [
                {
                    "id": str(item.id),
                    "report_id": str(item.report_id),
                    "reason": item.reason,
                    "status": item.status,
                    "created_at": _iso(item.created_at),
                    "resolved_at": _iso(item.resolved_at),
                    "resolution_reason": item.resolution_reason,
                }
                for item in appeals
            ],
            "reporter_reputation": (
                {
                    "score": reputation.score,
                    "approved_reports": reputation.approved_reports,
                    "rejected_reports": reputation.rejected_reports,
                }
                if reputation is not None
                else None
            ),
            "notification_preferences": (
                {
                    "parking_alerts_enabled": preferences.parking_alerts_enabled,
                    "background_location_enabled": preferences.background_location_enabled,
                    "push_enabled": preferences.push_enabled,
                    "quiet_start_hour": preferences.quiet_start_hour,
                    "quiet_end_hour": preferences.quiet_end_hour,
                    "timezone": preferences.timezone,
                    "updated_at": _iso(preferences.updated_at),
                }
                if preferences is not None
                else None
            ),
            "push_devices": [
                {
                    "id": str(item.id),
                    "platform": item.platform,
                    "enabled": item.enabled,
                    "updated_at": _iso(item.updated_at),
                }
                for item in devices
            ],
            "alert_deliveries": [
                {
                    "id": str(item.id),
                    "status": item.status,
                    "created_at": _iso(item.created_at),
                }
                for item in deliveries
            ],
            "consent_history": [
                {
                    "id": str(item.id),
                    "purpose": item.purpose,
                    "policy_version": item.policy_version,
                    "granted": item.granted,
                    "occurred_at": _iso(item.occurred_at),
                }
                for item in consent_events
            ],
            "data_rights_requests": [
                {
                    "id": str(item.id),
                    "request_type": item.request_type,
                    "status": item.status,
                    "requested_at": _iso(item.requested_at),
                    "completed_at": _iso(item.completed_at),
                }
                for item in requests
            ],
            "security_events": [
                {"action": item.action, "occurred_at": _iso(item.occurred_at)}
                for item in audit_events
            ],
        }

    async def active_media_keys(self, user_id: UUID) -> tuple[str, ...]:
        keys = await self._session.scalars(
            select(CommunityReportRow.photo_object_key).where(
                CommunityReportRow.reporter_id == user_id,
                CommunityReportRow.photo_object_key.is_not(None),
                CommunityReportRow.photo_deleted_at.is_(None),
            )
        )
        return tuple(key for key in keys if key is not None)

    async def delete_account(self, user_id: UUID) -> bool:
        await self._session.execute(
            update(AuditEventRow)
            .where(AuditEventRow.subject_id == user_id)
            .values(subject_id=None)
        )
        result = await self._session.execute(
            delete(UserRow).where(UserRow.id == user_id).returning(UserRow.id)
        )
        return result.scalar_one_or_none() is not None
