import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.identity.domain import Role, User
from app.modules.notifications.domain import DevicePlatform
from app.modules.notifications.providers import DisabledPushProvider
from app.modules.notifications.repositories import (
    InMemoryNotificationRepository,
    InMemoryPushProvider,
)
from app.modules.notifications.service import (
    InvalidNotificationPreference,
    NotificationService,
)
from app.modules.parking.domain import ParkingZone, Provenance, ZoneType
from app.modules.parking.service import ParkingMapService
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.notifications import notification_service


class ZoneRepository:
    def __init__(self, score: int | None) -> None:
        self.score = score

    async def in_viewport(
        self, west: float, south: float, east: float, north: float, limit: int
    ) -> tuple[ParkingZone, ...]:
        return ()

    async def at_location(self, longitude: float, latitude: float) -> ParkingZone | None:
        if self.score is None:
            return None
        return ParkingZone(
            uuid4(),
            "Tow-away curb",
            ZoneType.TOWING_HOTSPOT,
            '{"type":"Polygon","coordinates":[]}',
            self.score,
            Provenance.OFFICIAL,
            1.0,
            "Tow-away restriction is active.",
            25000,
            True,
            datetime.now(UTC),
            None,
        )


def _service(score: int | None = 20) -> tuple[
    NotificationService, InMemoryNotificationRepository, InMemoryPushProvider
]:
    repository = InMemoryNotificationRepository()
    provider = InMemoryPushProvider()
    return (
        NotificationService(repository, provider, ParkingMapService(ZoneRepository(score))),
        repository,
        provider,
    )


def test_alerts_require_explicit_separate_background_consent() -> None:
    async def scenario() -> None:
        service, _, _ = _service()
        user_id = uuid4()
        disabled = await service.evaluate_location(user_id, 25.7, -80.2)
        assert not disabled.should_alert
        with pytest.raises(InvalidNotificationPreference):
            await service.update_preferences(
                user_id,
                parking_alerts_enabled=False,
                background_location_enabled=True,
                push_enabled=False,
                quiet_start_hour=22,
                quiet_end_hour=7,
                timezone="UTC",
            )

    asyncio.run(scenario())


def test_high_risk_alert_pushes_once_and_records_delivery() -> None:
    async def scenario() -> None:
        service, repository, provider = _service(20)
        user_id = uuid4()
        await service.update_preferences(
            user_id,
            parking_alerts_enabled=True,
            background_location_enabled=True,
            push_enabled=True,
            quiet_start_hour=2,
            quiet_end_hour=3,
            timezone="UTC",
        )
        await service.register_device(user_id, DevicePlatform.IOS, "x" * 64)
        moment = datetime(2026, 7, 17, 12, tzinfo=UTC)
        first = await service.evaluate_location(user_id, 25.7, -80.2, moment)
        duplicate = await service.evaluate_location(user_id, 25.7, -80.2, moment)
        assert first.should_alert and first.parking_score == 20
        assert duplicate.deduplicated and not duplicate.should_alert
        assert len(provider.messages) == 1
        assert repository.deliveries[0][1] == "delivered"

    asyncio.run(scenario())


def test_quiet_hours_cross_midnight_and_safe_zone_suppress_warning() -> None:
    async def scenario() -> None:
        service, _, _ = _service(20)
        user_id = uuid4()
        await service.update_preferences(
            user_id,
            parking_alerts_enabled=True,
            background_location_enabled=True,
            push_enabled=False,
            quiet_start_hour=22,
            quiet_end_hour=7,
            timezone="America/New_York",
        )
        quiet = await service.evaluate_location(
            user_id, 25.7, -80.2, datetime(2026, 7, 17, 7, tzinfo=UTC)
        )
        assert not quiet.should_alert and "quiet" in quiet.reason.lower()

        safe_service, _, _ = _service(80)
        await safe_service.update_preferences(
            user_id,
            parking_alerts_enabled=True,
            background_location_enabled=True,
            push_enabled=False,
            quiet_start_hour=0,
            quiet_end_hour=0,
            timezone="UTC",
        )
        safe = await safe_service.evaluate_location(user_id, 25.7, -80.2)
        assert not safe.should_alert and safe.parking_score == 80

    asyncio.run(scenario())


def test_invalid_timezone_token_and_uncovered_location_are_safe_failures() -> None:
    async def scenario() -> None:
        service, _, _ = _service(None)
        user_id = uuid4()
        with pytest.raises(InvalidNotificationPreference):
            await service.update_preferences(
                user_id,
                parking_alerts_enabled=True,
                background_location_enabled=True,
                push_enabled=True,
                quiet_start_hour=22,
                quiet_end_hour=7,
                timezone="Mars/Olympus",
            )
        with pytest.raises(InvalidNotificationPreference):
            await service.register_device(user_id, DevicePlatform.ANDROID, "short")
        await service.update_preferences(
            user_id,
            parking_alerts_enabled=True,
            background_location_enabled=True,
            push_enabled=False,
            quiet_start_hour=0,
            quiet_end_hour=0,
            timezone="UTC",
        )
        uncovered = await service.evaluate_location(user_id, 25.7, -80.2)
        assert not uncovered.should_alert and uncovered.parking_score is None

    asyncio.run(scenario())


def test_notification_http_contract_updates_consent_registers_and_evaluates() -> None:
    service, _, _ = _service(20)
    user = User(
        uuid4(), "driver@example.com", "hash", Role.USER, True, True, datetime.now(UTC)
    )
    application = create_app()
    application.dependency_overrides[current_user] = lambda: user
    application.dependency_overrides[notification_service] = lambda: service
    with TestClient(application) as client:
        preferences = client.put(
            "/api/v1/notifications/preferences",
            json={
                "parking_alerts_enabled": True,
                "background_location_enabled": True,
                "push_enabled": True,
                "quiet_start_hour": 2,
                "quiet_end_hour": 3,
                "timezone": "UTC",
            },
        )
        device = client.post(
            "/api/v1/notifications/devices",
            json={"platform": "android", "token": "device-token-" + "x" * 32},
        )
        decision = client.post(
            "/api/v1/notifications/evaluate-location",
            json={"latitude": 25.7, "longitude": -80.2},
        )
    assert preferences.status_code == 200
    assert preferences.json()["background_location_enabled"] is True
    assert device.status_code == 201
    assert decision.status_code == 200
    assert decision.json()["parking_score"] == 20


def test_disabled_push_provider_fails_closed_without_external_configuration() -> None:
    async def scenario() -> None:
        service, repository, _ = _service()
        device = await service.register_device(uuid4(), DevicePlatform.IOS, "z" * 32)
        delivered = await DisabledPushProvider().send(device, "Title", "Body", {})
        assert delivered is False
        assert len(await repository.devices(device.user_id)) == 1

    asyncio.run(scenario())
