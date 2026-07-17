"""Repository contract tests at the SQLAlchemy adapter boundary."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import (
    AlertDeliveryRow,
    AuditEventRow,
    CommunityReportRow,
    DataRightsRequestRow,
    MunicipalImportBatchRow,
    MunicipalSourceRow,
    NotificationPreferenceRow,
    PrivacyConsentEventRow,
    PushDeviceRow,
    ReportAppealRow,
    ReporterReputationRow,
    SessionRow,
    UserRow,
)
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
from app.modules.ingestion.domain import (
    DataFormat,
    FeedKind,
    ImportBatch,
    ImportStatus,
    MunicipalSource,
    NormalizedImport,
    NormalizedParkingFacility,
    NormalizedParkingZone,
    RejectedRecord,
)
from app.modules.ingestion.sql_repository import SqlMunicipalIngestionRepository
from app.modules.parking.domain import ZoneType
from app.modules.privacy.domain import (
    ConsentDecision,
    ConsentPurpose,
    DataRequestStatus,
    DataRequestType,
    DataRightsRequest,
)
from app.modules.privacy.sql_repository import SqlPrivacyRepository


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


def test_sql_privacy_repository_writes_and_selects_latest_consents() -> None:
    async def scenario() -> None:
        db = session_mock()
        repository = SqlPrivacyRepository(db)
        user_id = uuid4()
        now = datetime.now(UTC)
        first = ConsentDecision(
            uuid4(), user_id, ConsentPurpose.PRODUCT_ANALYTICS, "v1", True, now
        )
        request = DataRightsRequest(
            uuid4(),
            user_id,
            "a" * 64,
            DataRequestType.EXPORT,
            DataRequestStatus.PROCESSING,
            now,
        )

        await repository.record_consent(first)
        await repository.add_request(request)
        await repository.complete_request(request.id, now)
        assert db.add.call_count == 2
        assert db.flush.await_count == 2

        latest_row = PrivacyConsentEventRow(
            id=uuid4(),
            user_id=user_id,
            purpose=ConsentPurpose.PRODUCT_ANALYTICS,
            policy_version="v2",
            granted=False,
            occurred_at=now + timedelta(seconds=1),
        )
        older_row = PrivacyConsentEventRow(
            id=first.id,
            user_id=user_id,
            purpose=first.purpose,
            policy_version=first.policy_version,
            granted=first.granted,
            occurred_at=first.occurred_at,
        )
        recommendation_row = PrivacyConsentEventRow(
            id=uuid4(),
            user_id=user_id,
            purpose=ConsentPurpose.PERSONALIZED_RECOMMENDATIONS,
            policy_version="v2",
            granted=True,
            occurred_at=now,
        )
        db.scalars.return_value = [recommendation_row, latest_row, older_row]

        decisions = await repository.latest_consents(user_id)
        assert len(decisions) == 2
        assert decisions[0].purpose is ConsentPurpose.PERSONALIZED_RECOMMENDATIONS
        assert decisions[1].granted is False

    asyncio.run(scenario())


def test_sql_privacy_export_minimizes_sensitive_fields_and_deletes_account() -> None:
    async def scenario() -> None:
        db = session_mock()
        repository = SqlPrivacyRepository(db)
        now = datetime.now(UTC)
        user_id, report_id = uuid4(), uuid4()
        user = UserRow(
            id=user_id,
            email="export@example.com",
            password_hash="never-export-this-password-hash",
            role="user",
            is_active=True,
            is_verified=True,
            created_at=now,
            mfa_secret="never-export-this-mfa-secret",
            mfa_enabled=True,
        )
        preferences = NotificationPreferenceRow(
            user_id=user_id,
            parking_alerts_enabled=True,
            background_location_enabled=True,
            push_enabled=True,
            quiet_start_hour=22,
            quiet_end_hour=7,
            timezone="UTC",
            updated_at=now,
        )
        reputation = ReporterReputationRow(
            user_id=user_id, score=0.75, approved_reports=2, rejected_reports=1
        )
        db.get.side_effect = [user, preferences, reputation]
        session = SessionRow(
            id=uuid4(), user_id=user_id, created_at=now, expires_at=now + timedelta(days=1)
        )
        report = CommunityReportRow(
            id=report_id,
            reporter_id=user_id,
            category="sign",
            latitude=25.7,
            longitude=-80.2,
            description="Complete sign evidence submitted by the account owner",
            status="pending",
            validation_score=0.7,
            fingerprint="f" * 64,
            photo_sha256="b" * 64,
            photo_object_key=f"community-reports/{report_id}/{'b' * 64}",
            photo_content_type="image/jpeg",
            photo_size_bytes=1024,
            photo_retained_until=now + timedelta(days=7),
            photo_deleted_at=None,
            moderation_reason=None,
            created_at=now,
            expires_at=now + timedelta(days=30),
        )
        appeal = ReportAppealRow(
            id=uuid4(),
            report_id=report_id,
            appellant_id=user_id,
            reason="Please review the full evidence",
            status="open",
            created_at=now,
            resolved_at=None,
            resolution_reason=None,
        )
        consent = PrivacyConsentEventRow(
            id=uuid4(),
            user_id=user_id,
            purpose="product_analytics",
            policy_version="v1",
            granted=False,
            occurred_at=now,
        )
        request = DataRightsRequestRow(
            id=uuid4(),
            user_id=user_id,
            subject_reference="c" * 64,
            request_type="export",
            status="processing",
            requested_at=now,
            completed_at=None,
        )
        device = PushDeviceRow(
            id=uuid4(),
            user_id=user_id,
            platform="ios",
            token_ciphertext="never-export-this-device-token",
            token_hash="d" * 64,
            enabled=True,
            updated_at=now,
        )
        delivery = AlertDeliveryRow(
            id=uuid4(),
            user_id=user_id,
            dedupe_key="never-export-this-dedupe-key",
            status="sent",
            created_at=now,
        )
        audit = AuditEventRow(
            id=uuid4(), action="session.login_succeeded", subject_id=user_id, occurred_at=now
        )
        db.scalars.side_effect = [
            [session],
            [report],
            [appeal],
            [consent],
            [request],
            [device],
            [delivery],
            [audit],
        ]

        exported = await repository.export_for_user(user_id)
        serialized = str(exported)
        assert exported["profile"] == {
            "id": str(user_id),
            "email": "export@example.com",
            "role": "user",
            "is_active": True,
            "is_verified": True,
            "mfa_enabled": True,
            "created_at": now.isoformat(),
        }
        assert "never-export" not in serialized
        assert "photo_object_key" not in serialized
        assert exported["reporter_reputation"] == {
            "score": 0.75,
            "approved_reports": 2,
            "rejected_reports": 1,
        }

        db.scalars.side_effect = None
        db.scalars.return_value = [report.photo_object_key, None]
        assert await repository.active_media_keys(user_id) == (report.photo_object_key,)

        missing = session_mock()
        missing.get.return_value = None
        with pytest.raises(ValueError, match="no longer exists"):
            await SqlPrivacyRepository(missing).export_for_user(user_id)

        updated = MagicMock()
        deleted = MagicMock()
        deleted.scalar_one_or_none.return_value = user_id
        db.execute.side_effect = [updated, deleted]
        assert await repository.delete_account(user_id)

        deleted.scalar_one_or_none.return_value = None
        db.execute.side_effect = [updated, deleted]
        assert not await repository.delete_account(user_id)

    asyncio.run(scenario())


def test_sql_municipal_repository_maps_sources_batches_and_import_records() -> None:
    async def scenario() -> None:
        db = session_mock()
        repository = SqlMunicipalIngestionRepository(db)
        now = datetime.now(UTC)
        source = MunicipalSource(
            uuid4(),
            "Synthetic source",
            "Test jurisdiction",
            FeedKind.PARKING_ZONES,
            DataFormat.GEOJSON,
            "https://example.test/feed",
            None,
            False,
            True,
            60,
            120,
            now,
            now,
        )
        await repository.add_source(source)
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

        source_row = MunicipalSourceRow(
            id=source.id,
            name=source.name,
            jurisdiction=source.jurisdiction,
            feed_kind=source.feed_kind,
            data_format=source.data_format,
            source_url=source.source_url,
            license_url=source.license_url,
            official=source.official,
            enabled=source.enabled,
            refresh_interval_minutes=source.refresh_interval_minutes,
            stale_after_minutes=source.stale_after_minutes,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )
        db.get.return_value = source_row
        assert await repository.source(source.id) == source
        db.scalars.return_value = [source_row]
        assert await repository.sources() == (source,)

        batch = ImportBatch(
            uuid4(),
            source.id,
            "a" * 64,
            "1.0",
            ImportStatus.PARTIAL,
            3,
            2,
            1,
            now,
            now,
        )
        batch_row = MunicipalImportBatchRow(
            id=batch.id,
            source_id=batch.source_id,
            content_sha256=batch.content_sha256,
            importer_version=batch.importer_version,
            status=batch.status,
            input_count=batch.input_count,
            accepted_count=batch.accepted_count,
            rejected_count=batch.rejected_count,
            received_at=batch.received_at,
            completed_at=batch.completed_at,
        )
        db.scalar.return_value = batch_row
        assert await repository.batch_by_digest(source.id, batch.content_sha256) == batch

        normalized = NormalizedImport(
            input_count=3,
            zones=(
                NormalizedParkingZone(
                    "zone-1",
                    "Synthetic zone",
                    ZoneType.GENERAL,
                    '{"type":"Polygon","coordinates":[[[-80.2,25.7],[-80.1,25.7],'
                    '[-80.1,25.8],[-80.2,25.7]]]}',
                    80,
                    None,
                    None,
                    False,
                    now,
                    now + timedelta(days=1),
                ),
            ),
            facilities=(
                NormalizedParkingFacility(
                    "facility-1",
                    "Synthetic garage",
                    "100 Test Ave",
                    25.7,
                    -80.2,
                    1000,
                    90,
                    1.0,
                    4.5,
                    10,
                    100,
                    "https://example.test/nav",
                    now,
                    now + timedelta(days=1),
                ),
            ),
            rejected=(RejectedRecord(2, "b" * 64, "invalid", "synthetic error"),),
        )
        await repository.commit_import(source, batch, normalized)
        assert db.add.call_count == 3
        assert db.flush.await_count == 2
        assert db.execute.await_count == 2

        db.scalars.return_value = [batch_row]
        assert await repository.batches(source.id, 10) == (batch,)

        missing = session_mock()
        missing.get.return_value = None
        missing.scalar.return_value = None
        assert await SqlMunicipalIngestionRepository(missing).source(uuid4()) is None
        assert (
            await SqlMunicipalIngestionRepository(missing).batch_by_digest(
                uuid4(), "c" * 64
            )
            is None
        )

    asyncio.run(scenario())
