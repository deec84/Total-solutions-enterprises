"""Repository contract tests at the SQLAlchemy adapter boundary."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import CommunityReportRow, SessionRow, UserRow
from app.modules.community.domain import (
    AppealStatus,
    CommunityReport,
    ReportAppeal,
    ReportCategory,
    ReportStatus,
)
from app.modules.community.sql_repository import SqlCommunityReportRepository
from app.modules.identity.audit import AuditAction, event
from app.modules.identity.domain import Role, User
from app.modules.identity.sql_repositories import (
    SqlAuditSink,
    SqlSessionRepository,
    SqlUserRepository,
)


def session_mock() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def user_row() -> UserRow:
    return UserRow(
        id=uuid4(),
        email="person@example.com",
        password_hash="hash",
        role="user",
        is_active=True,
        is_verified=False,
        created_at=datetime.now(UTC),
    )


def test_sql_user_repository_maps_reads_and_writes() -> None:
    async def scenario() -> None:
        db = session_mock()
        repository = SqlUserRepository(db)
        row = user_row()
        db.scalar.return_value = row
        db.get.return_value = row

        await repository.add(
            User(
                row.id,
                row.email,
                row.password_hash,
                Role.USER,
                True,
                False,
                row.created_at,
            )
        )
        by_email = await repository.get_by_email(row.email)
        by_id = await repository.get_by_id(row.id)

        assert by_email == by_id
        assert by_email is not None and by_email.role is Role.USER
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    asyncio.run(scenario())


def test_sql_user_repository_updates_and_missing_rows() -> None:
    async def scenario() -> None:
        db = session_mock()
        repository = SqlUserRepository(db)
        result = MagicMock()
        result.scalar_one_or_none.side_effect = [user_row(), user_row(), None]
        db.execute.return_value = result

        assert (await repository.mark_verified(uuid4())) is not None
        assert (await repository.update_password(uuid4(), "new-hash")) is not None
        assert await repository.mark_verified(uuid4()) is None

    asyncio.run(scenario())


def test_sql_session_repository_lifecycle_is_owner_scoped() -> None:
    async def scenario() -> None:
        db = session_mock()
        repository = SqlSessionRepository(db)
        token_id, user_id = uuid4(), uuid4()
        expires_at = datetime.now(UTC) + timedelta(days=1)
        await repository.add(token_id, user_id, expires_at)

        result = MagicMock()
        result.scalar_one_or_none.side_effect = [user_id, token_id, None]
        db.execute.return_value = result
        assert await repository.consume(token_id) == user_id
        await repository.revoke(token_id)
        await repository.revoke_all(user_id)
        assert await repository.revoke_for_user(token_id, user_id) is True
        assert await repository.revoke_for_user(uuid4(), user_id) is False

        row = SessionRow(
            id=token_id,
            user_id=user_id,
            created_at=datetime.now(UTC),
            expires_at=expires_at,
        )
        db.scalars.return_value = [row]
        sessions = await repository.list_for_user(user_id)
        assert sessions[0].id == token_id

    asyncio.run(scenario())


def test_sql_audit_sink_flushes_append_only_event() -> None:
    async def scenario() -> None:
        db = session_mock()
        sink = SqlAuditSink(db)
        await sink.record(event(AuditAction.LOGIN_SUCCEEDED, uuid4()))
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    asyncio.run(scenario())


def test_sql_community_repository_flushes_rows_before_followup_updates() -> None:
    async def scenario() -> None:
        db = session_mock()
        repository = SqlCommunityReportRepository(db)
        reporter_id, report_id, appeal_id = uuid4(), uuid4(), uuid4()
        created_at = datetime.now(UTC)
        await repository.add(
            CommunityReport(
                report_id,
                reporter_id,
                ReportCategory.TOWING,
                25.7617,
                -80.1918,
                "Tow truck removed a vehicle beside this curb",
                ReportStatus.PENDING,
                0.65,
                "fingerprint",
                None,
                created_at,
                created_at + timedelta(days=30),
            )
        )
        await repository.add_appeal(
            ReportAppeal(
                appeal_id,
                report_id,
                reporter_id,
                "The original uncropped image is available",
                AppealStatus.OPEN,
                created_at,
            )
        )

        assert db.add.call_count == 2
        assert db.flush.await_count == 2

    asyncio.run(scenario())


def test_sql_community_repository_maps_media_retention_and_deletion() -> None:
    async def scenario() -> None:
        db = session_mock()
        repository = SqlCommunityReportRepository(db)
        now = datetime.now(UTC)
        row = CommunityReportRow(
            id=uuid4(),
            reporter_id=uuid4(),
            category=ReportCategory.SIGN,
            latitude=25.7617,
            longitude=-80.1918,
            description="The complete parking sign is visible in this evidence",
            status=ReportStatus.PENDING,
            validation_score=0.75,
            fingerprint="f" * 64,
            photo_sha256="a" * 64,
            photo_object_key=f"community-reports/{uuid4()}/{'a' * 64}",
            photo_content_type="image/png",
            photo_size_bytes=4096,
            photo_retained_until=now - timedelta(minutes=1),
            photo_deleted_at=None,
            moderation_reason=None,
            created_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=29),
        )
        db.scalars.return_value = [row]

        expired = await repository.expired_media(now, 10)

        assert expired[0].photo_available
        assert expired[0].photo_object_key == row.photo_object_key
        deleted_at = datetime.now(UTC)
        row.photo_deleted_at = deleted_at
        db.get.return_value = row
        deleted = await repository.mark_photo_deleted(row.id, deleted_at)
        assert deleted is not None and not deleted.photo_available
        assert deleted.photo_deleted_at == deleted_at

    asyncio.run(scenario())
