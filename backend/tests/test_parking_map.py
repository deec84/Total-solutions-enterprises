"""Parking score semantics and viewport API contracts."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.identity.domain import Role, User
from app.modules.parking.domain import (
    ParkingZone,
    Provenance,
    RiskLevel,
    ZoneType,
    risk_level,
)
from app.modules.parking.service import InvalidViewportError, ParkingMapService
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.parking import parking_map_service


class FakeZoneRepository:
    def __init__(self, zones: tuple[ParkingZone, ...]) -> None:
        self.zones = zones
        self.received_limit: int | None = None

    async def in_viewport(
        self, west: float, south: float, east: float, north: float, limit: int
    ) -> tuple[ParkingZone, ...]:
        self.received_limit = limit
        return self.zones

    async def at_location(self, longitude: float, latitude: float) -> ParkingZone | None:
        return self.zones[0] if self.zones else None


def zone(score: int = 95) -> ParkingZone:
    return ParkingZone(
        id=uuid4(),
        name="Official curb zone",
        zone_type=ZoneType.GENERAL,
        geometry_geojson=(
            '{"type":"Polygon","coordinates":[[[-80.2,25.7],[-80.1,25.7],'
            '[-80.1,25.8],[-80.2,25.8],[-80.2,25.7]]]}'
        ),
        parking_score=score,
        provenance=Provenance.OFFICIAL,
        confidence=1.0,
        restriction_summary="No active restriction",
        average_towing_cost_cents=18500,
        towing_hotspot=False,
        observed_at=datetime.now(UTC),
        expires_at=None,
    )


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (95, RiskLevel.VERY_SAFE),
        (80, RiskLevel.SAFE),
        (60, RiskLevel.READ_SIGNS),
        (40, RiskLevel.HIGH_RISK),
        (20, RiskLevel.VERY_HIGH_RISK),
        (0, RiskLevel.DO_NOT_PARK),
    ],
)
def test_score_bands(score: int, expected: RiskLevel) -> None:
    assert risk_level(score) is expected


def test_rejects_invalid_score_and_viewport() -> None:
    with pytest.raises(ValueError):
        risk_level(101)

    async def scenario() -> None:
        service = ParkingMapService(FakeZoneRepository(()))
        with pytest.raises(InvalidViewportError):
            await service.viewport(-80, 25, -81, 26)

    asyncio.run(scenario())


def test_authenticated_viewport_contract_and_limit_bounding() -> None:
    repository = FakeZoneRepository((zone(),))
    application = create_app()
    application.dependency_overrides[current_user] = lambda: User(
        uuid4(),
        "driver@example.com",
        "hash",
        Role.USER,
        True,
        True,
        datetime.now(UTC),
    )
    application.dependency_overrides[parking_map_service] = lambda: ParkingMapService(
        repository
    )
    with TestClient(application) as client:
        response = client.get(
            "/api/v1/parking/zones",
            params={"west": -80.3, "south": 25.6, "east": -80.0, "north": 25.9},
        )

    assert response.status_code == 200
    payload = response.json()["zones"][0]
    assert payload["parking_score"] == 95
    assert payload["risk_level"] == "very_safe"
    assert payload["provenance"] == "official"
    assert payload["zone_type"] == "general"
    assert payload["geometry"]["type"] == "Polygon"
    assert repository.received_limit == 500
    assert response.headers["Cache-Control"].startswith("private, max-age=30")


def test_point_decision_returns_trust_metadata() -> None:
    repository = FakeZoneRepository((zone(40),))
    application = create_app()
    application.dependency_overrides[current_user] = lambda: User(
        uuid4(),
        "driver@example.com",
        "hash",
        Role.USER,
        True,
        True,
        datetime.now(UTC),
    )
    application.dependency_overrides[parking_map_service] = lambda: ParkingMapService(
        repository
    )
    with TestClient(application) as client:
        response = client.get(
            "/api/v1/parking/decision",
            params={"latitude": 25.7617, "longitude": -80.1918},
        )

    assert response.status_code == 200
    assert response.json()["covered"] is True
    assert response.json()["zone"]["risk_level"] == "high_risk"
    assert response.json()["zone"]["confidence"] == 1.0
    assert response.headers["Cache-Control"] == "no-store"
