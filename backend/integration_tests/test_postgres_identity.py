"""Identity persistence integration against a migrated PostgreSQL/PostGIS instance."""

import asyncio
import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import pytest
from geoalchemy2.elements import WKTElement
from sqlalchemy import delete, select, text

from app.infrastructure.database import engine, session_factory
from app.infrastructure.models import (
    AdminAuditRow,
    AlertDeliveryRow,
    BillingEventRow,
    BillingSubscriptionRow,
    DataRightsRequestRow,
    LoginRateLimitRow,
    MunicipalImportBatchRow,
    MunicipalSourceRow,
    ParkingFacilityRow,
    ParkingZoneRow,
    PushDeviceRow,
    UserRow,
)
from app.main import create_app
from app.modules.admin.sql_audit import SqlAdminAuditTrail
from app.modules.billing.domain import (
    BillingProduct,
    EntitlementCode,
    PurchaseVerificationRequest,
    StoreEnvironment,
    StorePlatform,
    SubscriptionStatus,
    VerifiedPurchase,
)
from app.modules.billing.service import BillingService
from app.modules.billing.sql_repository import SqlBillingRepository
from app.modules.community.domain import ReportCategory, ReportStatus
from app.modules.community.service import CommunityReportService
from app.modules.community.sql_repository import SqlCommunityReportRepository
from app.modules.identity.abuse import RateLimitExceeded
from app.modules.identity.domain import Role, User
from app.modules.identity.security import PasswordManager
from app.modules.identity.sql_abuse import SqlLoginRateLimiter
from app.modules.identity.sql_repositories import SqlSessionRepository, SqlUserRepository
from app.modules.ingestion.connectors import (
    CsvParkingFacilityConnector,
    GeoJsonParkingZoneConnector,
)
from app.modules.ingestion.domain import DataFormat, FeedKind, ImportStatus
from app.modules.ingestion.service import MunicipalIngestionService
from app.modules.ingestion.sql_repository import SqlMunicipalIngestionRepository
from app.modules.notifications.domain import (
    DevicePlatform,
    NotificationPreferences,
    PushDevice,
)
from app.modules.notifications.sql_repository import SqlNotificationRepository
from app.modules.parking.sql_repository import SqlParkingZoneRepository
from app.modules.privacy.domain import ConsentPurpose
from app.modules.privacy.service import (
    ACCOUNT_DELETION_CONFIRMATION,
    PrivacyService,
)
from app.modules.privacy.sql_repository import SqlPrivacyRepository
from app.modules.recommendations.sql_repository import SqlParkingFacilityRepository


def run_isolated_scenario(scenario: Callable[[], Awaitable[None]]) -> None:
    async def execute() -> None:
        try:
            await scenario()
        finally:
            await engine.dispose()

    asyncio.run(execute())


def test_migrated_postgis_identity_repository_round_trip() -> None:
    async def scenario() -> None:
        user_id, token_id = uuid4(), uuid4()
        email = f"integration-{user_id}@example.com"
        async with session_factory() as session, session.begin():
            postgis_version = await session.scalar(text("SELECT postgis_version()"))
            assert postgis_version
            users = SqlUserRepository(session)
            sessions = SqlSessionRepository(session)
            await users.add(
                User(
                    user_id,
                    email,
                    "argon2-hash",
                    Role.USER,
                    True,
                    False,
                    datetime.now(UTC),
                )
            )
            await sessions.add(token_id, user_id, datetime.now(UTC) + timedelta(days=1))

        async with session_factory() as session, session.begin():
            users = SqlUserRepository(session)
            sessions = SqlSessionRepository(session)
            stored = await users.get_by_email(email)
            assert stored is not None and stored.id == user_id
            assert len(await sessions.list_for_user(user_id)) == 1
            assert await sessions.consume(token_id) == user_id
            await session.execute(delete(UserRow).where(UserRow.id == user_id))

    run_isolated_scenario(scenario)


def test_postgis_zone_viewport_and_point_queries() -> None:
    async def scenario() -> None:
        zone_id = uuid4()
        async with session_factory() as session, session.begin():
            session.add(
                ParkingZoneRow(
                    id=zone_id,
                    name="Integration curb zone",
                    zone_type="towing_hotspot",
                    geometry=WKTElement(
                        "POLYGON((-80.20 25.70,-80.10 25.70,-80.10 25.80,"
                        "-80.20 25.80,-80.20 25.70))",
                        srid=4326,
                    ),
                    parking_score=20,
                    provenance="official",
                    confidence=1.0,
                    restriction_summary="Tow-away zone",
                    average_towing_cost_cents=25000,
                    towing_hotspot=True,
                    observed_at=datetime.now(UTC),
                    expires_at=None,
                )
            )

        async with session_factory() as session, session.begin():
            repository = SqlParkingZoneRepository(session)
            zones = await repository.in_viewport(-80.3, 25.6, -80.0, 25.9, 100)
            decision = await repository.at_location(-80.15, 25.75)
            assert any(zone.id == zone_id for zone in zones)
            assert decision is not None and decision.id == zone_id
            assert decision.towing_hotspot is True
            await session.execute(delete(ParkingZoneRow).where(ParkingZoneRow.id == zone_id))

    run_isolated_scenario(scenario)


def test_authentication_http_round_trip_uses_postgresql() -> None:
    async def scenario() -> None:
        application = create_app()
        transport = httpx.ASGITransport(app=application)
        email = f"http-{uuid4()}@example.com"
        credentials = {"email": email, "password": "integration-password"}
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            registration = await client.post("/api/v1/auth/register", json=credentials)
            assert registration.status_code == 201

            async with session_factory() as session, session.begin():
                users = SqlUserRepository(session)
                stored = await users.get_by_email(email)
                assert stored is not None
                await users.mark_verified(stored.id)

            login = await client.post("/api/v1/auth/login", json=credentials)
            assert login.status_code == 200
            access_token = login.json()["access_token"]
            profile = await client.get(
                "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
            )
            readiness = await client.get("/api/v1/health/ready")
            assert profile.status_code == 200
            assert readiness.status_code == 200

            async with session_factory() as session, session.begin():
                await session.execute(delete(UserRow).where(UserRow.email == email))

    run_isolated_scenario(scenario)


def test_community_report_reputation_and_appeal_round_trip() -> None:
    async def scenario() -> None:
        user_id = uuid4()
        async with session_factory() as session, session.begin():
            await SqlUserRepository(session).add(
                User(
                    user_id,
                    f"community-{user_id}@example.com",
                    "argon2-hash",
                    Role.USER,
                    True,
                    True,
                    datetime.now(UTC),
                )
            )
            repository = SqlCommunityReportRepository(session)
            service = CommunityReportService(repository)
            report = await service.submit(
                user_id,
                ReportCategory.TOWING,
                25.7617,
                -80.1918,
                "A tow truck removed a vehicle beside this curb after ten PM",
            )
            assert report.status is ReportStatus.PENDING
            await service.moderate(report.id, False, "Evidence needs a wider photo")
            appeal = await service.appeal(
                report.id, user_id, "The original uncropped image is available"
            )
            await service.resolve_appeal(
                appeal.id, True, "Original image confirms the towing report"
            )

        async with session_factory() as session, session.begin():
            repository = SqlCommunityReportRepository(session)
            stored = await repository.get(report.id)
            reputation = await repository.reputation(user_id)
            assert stored is not None and stored.status is ReportStatus.PUBLISHED
            assert reputation.approved_reports == 1
            assert reputation.rejected_reports == 1
            await session.execute(delete(UserRow).where(UserRow.id == user_id))

    run_isolated_scenario(scenario)


def test_admin_mfa_is_encrypted_and_audit_chain_is_persistent() -> None:
    async def scenario() -> None:
        user_id = uuid4()
        rfc_totp_seed = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        async with session_factory() as session, session.begin():
            users = SqlUserRepository(session)
            await users.add(
                User(
                    user_id,
                    f"admin-{user_id}@example.com",
                    "argon2-hash",
                    Role.ADMIN,
                    True,
                    True,
                    datetime.now(UTC),
                )
            )
            updated = await users.set_mfa(user_id, rfc_totp_seed, True)
            assert updated is not None and updated.mfa_secret == rfc_totp_seed
            await SqlAdminAuditTrail(session).append(
                user_id, "admin.integration_test", user_id
            )

        async with session_factory() as session, session.begin():
            raw_secret = await session.scalar(
                select(UserRow.mfa_secret).where(UserRow.id == user_id)
            )
            assert raw_secret is not None and raw_secret != rfc_totp_seed
            valid, checked = await SqlAdminAuditTrail(session).verify_integrity()
            assert valid and checked >= 1
            await session.execute(
                delete(AdminAuditRow).where(AdminAuditRow.actor_id == user_id)
            )
            await session.execute(delete(UserRow).where(UserRow.id == user_id))

    run_isolated_scenario(scenario)


def test_notification_consent_encrypted_device_and_atomic_deduplication() -> None:
    async def scenario() -> None:
        user_id, device_id = uuid4(), uuid4()
        token = "integration-device-token-" + "x" * 40
        now = datetime.now(UTC)
        async with session_factory() as session, session.begin():
            await SqlUserRepository(session).add(
                User(
                    user_id,
                    f"alerts-{user_id}@example.com",
                    "argon2-hash",
                    Role.USER,
                    True,
                    True,
                    now,
                )
            )
            repository = SqlNotificationRepository(session)
            await repository.save_preferences(
                NotificationPreferences(user_id, True, True, True, 22, 7, "UTC", now)
            )
            await repository.register_device(
                PushDevice(device_id, user_id, DevicePlatform.ANDROID, token, True, now)
            )
            assert await repository.claim_delivery(user_id, "dedupe-key", now)
            assert not await repository.claim_delivery(user_id, "dedupe-key", now)

        async with session_factory() as session, session.begin():
            repository = SqlNotificationRepository(session)
            preferences = await repository.preferences(user_id)
            devices = await repository.devices(user_id)
            raw_token = await session.scalar(
                select(PushDeviceRow.token_ciphertext).where(PushDeviceRow.id == device_id)
            )
            assert preferences.background_location_enabled
            assert devices[0].token == token
            assert raw_token is not None and token not in raw_token
            await session.execute(
                delete(AlertDeliveryRow).where(AlertDeliveryRow.user_id == user_id)
            )
            await session.execute(delete(UserRow).where(UserRow.id == user_id))

    run_isolated_scenario(scenario)


def test_privacy_export_and_account_deletion_use_database_cascades() -> None:
    async def scenario() -> None:
        user_id = uuid4()
        passwords = PasswordManager()
        subject = User(
            user_id,
            f"privacy-{user_id}@example.com",
            passwords.hash("integration-password"),
            Role.USER,
            True,
            True,
            datetime.now(UTC),
        )
        async with session_factory() as session, session.begin():
            await SqlUserRepository(session).add(subject)
            privacy = PrivacyService(
                SqlPrivacyRepository(session),
                passwords,
                "integration-subject-secret",
                "integration-v1",
            )
            await privacy.decide_consent(
                user_id, ConsentPurpose.PRODUCT_ANALYTICS, False
            )
            export = await privacy.export(user_id)
            assert export.data["profile"] == {
                "id": str(user_id),
                "email": subject.email,
                "role": "user",
                "is_active": True,
                "is_verified": True,
                "mfa_enabled": False,
                "created_at": subject.created_at.isoformat(),
            }
            assert "password_hash" not in str(export.data)
            deletion_request_id = await privacy.delete_account(
                subject,
                "integration-password",
                ACCOUNT_DELETION_CONFIRMATION,
            )

        async with session_factory() as session, session.begin():
            assert await session.get(UserRow, user_id) is None
            retained_request = await session.get(
                DataRightsRequestRow, deletion_request_id
            )
            assert retained_request is not None
            assert retained_request.user_id is None
            assert retained_request.status == "completed"
            assert retained_request.subject_reference != str(user_id)
            await session.execute(
                delete(DataRightsRequestRow).where(
                    DataRightsRequestRow.subject_reference
                    == retained_request.subject_reference
                )
            )

    run_isolated_scenario(scenario)


def test_governed_municipal_import_upserts_synthetic_postgis_records() -> None:
    async def scenario() -> None:
        connectors = {
            (FeedKind.PARKING_ZONES, DataFormat.GEOJSON): GeoJsonParkingZoneConnector(),
            (FeedKind.PARKING_FACILITIES, DataFormat.CSV): CsvParkingFacilityConnector(),
        }
        async with session_factory() as session, session.begin():
            ingestion = MunicipalIngestionService(
                SqlMunicipalIngestionRepository(session), connectors, 1024 * 1024
            )
            zone_source = await ingestion.create_source(
                name="SYNTHETIC Miami-Dade zones",
                jurisdiction="Synthetic test jurisdiction",
                feed_kind=FeedKind.PARKING_ZONES,
                data_format=DataFormat.GEOJSON,
                source_url="https://example.test/zones.geojson",
                license_url=None,
                official=False,
                refresh_interval_minutes=60,
                stale_after_minutes=120,
            )
            zone_payload = json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "external_id": "synthetic-zone-integration",
                                "name": "SYNTHETIC ZONE — NOT OFFICIAL",
                                "zone_type": "general",
                                "parking_score": 80,
                                "observed_at": "2026-07-17T12:00:00Z",
                                "expires_at": "2026-07-18T12:00:00Z",
                            },
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [
                                        [-80.20, 25.70],
                                        [-80.10, 25.70],
                                        [-80.10, 25.80],
                                        [-80.20, 25.70],
                                    ]
                                ],
                            },
                        }
                    ],
                }
            ).encode()
            zone_batch = await ingestion.import_payload(zone_source.id, zone_payload)
            assert zone_batch.status is ImportStatus.COMMITTED
            replay = await ingestion.import_payload(zone_source.id, zone_payload)
            assert replay.id == zone_batch.id

            facility_source = await ingestion.create_source(
                name="SYNTHETIC Broward facilities",
                jurisdiction="Synthetic test jurisdiction",
                feed_kind=FeedKind.PARKING_FACILITIES,
                data_format=DataFormat.CSV,
                source_url="https://example.test/facilities.csv",
                license_url=None,
                official=False,
                refresh_interval_minutes=60,
                stale_after_minutes=120,
            )
            facility_payload = (
                "external_id,name,address,latitude,longitude,hourly_price_cents,"
                "safety_score,towing_incidents_per_1000,rating,available_spaces,capacity,"
                "navigation_url,observed_at,expires_at\n"
                "synthetic-facility-integration,SYNTHETIC GARAGE — NOT OFFICIAL,"
                "100 Test Ave,25.7617,-80.1918,1200,90,1.5,4.5,10,100,"
                "https://example.test/nav,2026-07-17T12:00:00Z,"
                "2026-07-18T12:00:00Z\n"
            ).encode()
            facility_batch = await ingestion.import_payload(
                facility_source.id, facility_payload
            )
            assert facility_batch.status is ImportStatus.COMMITTED

        async with session_factory() as session, session.begin():
            zone = await session.scalar(
                select(ParkingZoneRow).where(
                    ParkingZoneRow.source_id == zone_source.id
                )
            )
            facility = await session.scalar(
                select(ParkingFacilityRow).where(
                    ParkingFacilityRow.source_id == facility_source.id
                )
            )
            assert zone is not None
            assert zone.provenance == "estimated"
            assert zone.import_batch_id == zone_batch.id
            assert facility is not None
            assert facility.provenance == "estimated"
            assert facility.import_batch_id == facility_batch.id
            await session.execute(
                delete(ParkingZoneRow).where(ParkingZoneRow.source_id == zone_source.id)
            )
            await session.execute(
                delete(ParkingFacilityRow).where(
                    ParkingFacilityRow.source_id == facility_source.id
                )
            )
            await session.execute(
                delete(MunicipalImportBatchRow).where(
                    MunicipalImportBatchRow.source_id.in_(
                        [zone_source.id, facility_source.id]
                    )
                )
            )
            await session.execute(
                delete(MunicipalSourceRow).where(
                    MunicipalSourceRow.id.in_([zone_source.id, facility_source.id])
                )
            )

    run_isolated_scenario(scenario)


def test_verified_billing_ledger_survives_account_deletion_without_store_identifiers() -> None:
    class SyntheticVerifier:
        def __init__(self, evidence: VerifiedPurchase) -> None:
            self._evidence = evidence

        async def verify(
            self, request: PurchaseVerificationRequest
        ) -> VerifiedPurchase:
            return self._evidence

    async def scenario() -> None:
        user_id = uuid4()
        passwords = PasswordManager()
        subject = User(
            user_id,
            f"billing-{user_id}@example.com",
            passwords.hash("integration-password"),
            Role.USER,
            True,
            True,
            datetime.now(UTC),
        )
        now = datetime.now(UTC)
        evidence = VerifiedPurchase(
            user_id,
            StorePlatform.APPLE_APP_STORE,
            "ai.parkshield.synthetic.premium",
            EntitlementCode.PREMIUM,
            SubscriptionStatus.ACTIVE,
            StoreEnvironment.SANDBOX,
            f"synthetic-provider-event-{user_id}",
            f"synthetic-store-transaction-{user_id}",
            f"synthetic-store-original-{user_id}",
            now - timedelta(minutes=1),
            now + timedelta(days=30),
            now,
            True,
        )
        async with session_factory() as session, session.begin():
            await SqlUserRepository(session).add(subject)
            billing = BillingService(
                SqlBillingRepository(session),
                SyntheticVerifier(evidence),
                "integration-billing-subject-secret-at-least-32-characters",
                (
                    BillingProduct(
                        StorePlatform.APPLE_APP_STORE,
                        evidence.product_id,
                        EntitlementCode.PREMIUM,
                    ),
                ),
                True,
                frozenset({StoreEnvironment.SANDBOX}),
            )
            entitlement = await billing.verify_purchase(
                user_id,
                StorePlatform.APPLE_APP_STORE,
                evidence.product_id,
                "SYNTHETIC PAYLOAD — NOT A REAL RECEIPT",
            )
            assert entitlement.tier == "premium"
            export = await PrivacyService(
                SqlPrivacyRepository(session),
                passwords,
                "integration-privacy-subject-secret",
                "integration-v1",
            ).export(user_id)
            assert export.data["store_subscriptions"][0]["status"] == "active"

        async with session_factory() as session, session.begin():
            privacy = PrivacyService(
                SqlPrivacyRepository(session),
                passwords,
                "integration-privacy-subject-secret",
                "integration-v1",
            )
            deletion_request_id = await privacy.delete_account(
                subject,
                "integration-password",
                ACCOUNT_DELETION_CONFIRMATION,
            )

        async with session_factory() as session, session.begin():
            retained = await session.scalar(
                select(BillingSubscriptionRow).where(
                    BillingSubscriptionRow.subject_reference.is_not(None),
                    BillingSubscriptionRow.product_id == evidence.product_id,
                )
            )
            assert retained is not None
            assert retained.user_id is None
            assert retained.transaction_reference != evidence.transaction_id
            assert retained.original_transaction_reference != evidence.original_transaction_id
            await session.execute(
                delete(BillingEventRow).where(
                    BillingEventRow.subscription_id == retained.id
                )
            )
            await session.execute(
                delete(BillingSubscriptionRow).where(
                    BillingSubscriptionRow.id == retained.id
                )
            )
            await session.execute(
                delete(DataRightsRequestRow).where(
                    DataRightsRequestRow.id == deletion_request_id
                )
            )

    run_isolated_scenario(scenario)


def test_cross_feature_driver_journey_uses_migrated_postgresql() -> None:
    async def scenario() -> None:
        application = create_app()
        transport = httpx.ASGITransport(app=application)
        email = f"journey-{uuid4()}@example.com"
        credentials = {"email": email, "password": "integration-password"}
        zone_id = uuid4()
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            registration = await client.post("/api/v1/auth/register", json=credentials)
            assert registration.status_code == 201
            async with session_factory() as session, session.begin():
                users = SqlUserRepository(session)
                user = await users.get_by_email(email)
                assert user is not None
                await users.mark_verified(user.id)
                session.add(
                    ParkingZoneRow(
                        id=zone_id,
                        name="Journey towing zone",
                        zone_type="towing_hotspot",
                        geometry=WKTElement(
                            "POLYGON((-80.20 25.70,-80.10 25.70,-80.10 25.80,"
                            "-80.20 25.80,-80.20 25.70))",
                            srid=4326,
                        ),
                        parking_score=20,
                        provenance="official",
                        confidence=1.0,
                        restriction_summary="Tow-away restriction",
                        average_towing_cost_cents=25000,
                        towing_hotspot=True,
                        observed_at=datetime.now(UTC),
                        expires_at=None,
                    )
                )
            login = await client.post("/api/v1/auth/login", json=credentials)
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            map_decision = await client.get(
                "/api/v1/parking/decision",
                params={"latitude": 25.75, "longitude": -80.15},
                headers=headers,
            )
            assistant = await client.post(
                "/api/v1/ai/parking-assistant",
                json={
                    "question": "Can I park here?",
                    "latitude": 25.75,
                    "longitude": -80.15,
                    "has_resident_permit": False,
                },
                headers=headers,
            )
            preferences = await client.put(
                "/api/v1/notifications/preferences",
                json={
                    "parking_alerts_enabled": True,
                    "background_location_enabled": True,
                    "push_enabled": False,
                    "quiet_start_hour": 0,
                    "quiet_end_hour": 0,
                    "timezone": "UTC",
                },
                headers=headers,
            )
            alert = await client.post(
                "/api/v1/notifications/evaluate-location",
                json={"latitude": 25.75, "longitude": -80.15},
                headers=headers,
            )
            report = await client.post(
                "/api/v1/reports",
                json={
                    "category": "towing",
                    "latitude": 25.75,
                    "longitude": -80.15,
                    "description": "Tow truck activity observed at this curb tonight",
                },
                headers=headers,
            )
            assert map_decision.json()["zone"]["parking_score"] == 20
            assert assistant.json()["recommendation"] == "do_not_park"
            assert preferences.status_code == 200
            assert alert.json()["should_alert"] is True
            assert report.status_code == 201

        async with session_factory() as session, session.begin():
            await session.execute(delete(ParkingZoneRow).where(ParkingZoneRow.id == zone_id))
            await session.execute(delete(UserRow).where(UserRow.email == email))
    run_isolated_scenario(scenario)


def test_postgis_nearby_parking_facility_recommendation_query() -> None:
    async def scenario() -> None:
        facility_id = uuid4()
        async with session_factory() as session, session.begin():
            session.add(
                ParkingFacilityRow(
                    id=facility_id,
                    name="Integration parking garage",
                    address="100 Integration Way, Miami, FL",
                    location=WKTElement("POINT(-80.1918 25.7618)", srid=4326),
                    hourly_price_cents=1200,
                    safety_score=92,
                    towing_incidents_per_1000=2,
                    rating=4.7,
                    available_spaces=15,
                    capacity=100,
                    navigation_url="https://maps.example.com/integration-garage",
                    provenance="official",
                    confidence=0.98,
                    observed_at=datetime.now(UTC),
                    expires_at=None,
                )
            )

        async with session_factory() as session, session.begin():
            candidates = await SqlParkingFacilityRepository(session).nearby(
                -80.1918, 25.7617, 1500, 10
            )
            match = next(item for item in candidates if item.facility.id == facility_id)
            assert match.walking_distance_meters < 100
            assert match.facility.provenance.value == "official"
            await session.execute(
                delete(ParkingFacilityRow).where(ParkingFacilityRow.id == facility_id)
            )

    run_isolated_scenario(scenario)


def test_login_rate_limit_is_shared_across_database_sessions() -> None:
    async def scenario() -> None:
        key = uuid4().hex.ljust(64, "0")
        async with session_factory() as session, session.begin():
            limiter = SqlLoginRateLimiter(session)
            for _ in range(5):
                await limiter.record_failure(key)

        async with session_factory() as session, session.begin():
            with pytest.raises(RateLimitExceeded):
                await SqlLoginRateLimiter(session).check(key)
            await session.execute(
                delete(LoginRateLimitRow).where(LoginRateLimitRow.key == key)
            )

    run_isolated_scenario(scenario)
