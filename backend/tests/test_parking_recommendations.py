import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import ParkingFacilityRow
from app.main import create_app
from app.modules.identity.domain import Role, User
from app.modules.parking.domain import Provenance
from app.modules.recommendations.domain import ParkingFacility
from app.modules.recommendations.repositories import InMemoryParkingFacilityRepository
from app.modules.recommendations.service import ParkingRecommendationService
from app.modules.recommendations.sql_repository import SqlParkingFacilityRepository
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.recommendations import recommendation_service


def facility(
    name: str,
    *,
    latitude: float = 25.7618,
    hourly_price_cents: int | None = 1200,
    safety_score: int = 90,
    towing_incidents: float = 2,
    rating: float | None = 4.5,
    available_spaces: int | None = 20,
    capacity: int | None = 100,
    expires_at: datetime | None = None,
) -> ParkingFacility:
    return ParkingFacility(
        id=uuid4(),
        name=name,
        address="100 Safe Parking Way, Miami, FL",
        latitude=latitude,
        longitude=-80.1918,
        hourly_price_cents=hourly_price_cents,
        safety_score=safety_score,
        towing_incidents_per_1000=towing_incidents,
        rating=rating,
        available_spaces=available_spaces,
        capacity=capacity,
        navigation_url="https://maps.example.com/safe-parking",
        provenance=Provenance.OFFICIAL,
        confidence=0.95,
        observed_at=datetime.now(UTC),
        expires_at=expires_at,
    )


def test_recommendations_rank_safety_and_low_towing_above_a_risky_option() -> None:
    async def scenario() -> None:
        safe = facility("Safe garage")
        risky = facility(
            "Risky curb",
            latitude=25.76171,
            hourly_price_cents=0,
            safety_score=25,
            towing_incidents=40,
            rating=5,
            available_spaces=80,
        )
        service = ParkingRecommendationService(
            InMemoryParkingFacilityRepository((risky, safe))
        )
        recommendations = await service.nearby(-80.1918, 25.7617)
        assert recommendations[0].facility.name == "Safe garage"
        assert recommendations[0].ranking_score > recommendations[1].ranking_score
        assert "Low historical towing" in " ".join(recommendations[0].reasons)

    asyncio.run(scenario())


def test_recommendations_apply_budget_expiry_radius_and_limit() -> None:
    async def scenario() -> None:
        facilities = (
            facility("Within budget", hourly_price_cents=800),
            facility("Unknown price", hourly_price_cents=None),
            facility("Over budget", hourly_price_cents=2000),
            facility(
                "Expired",
                hourly_price_cents=500,
                expires_at=datetime.now(UTC) - timedelta(minutes=1),
            ),
            facility("Far away", latitude=26.0, hourly_price_cents=500),
        )
        service = ParkingRecommendationService(InMemoryParkingFacilityRepository(facilities))
        recommendations = await service.nearby(
            -80.1918,
            25.7617,
            radius_meters=1000,
            max_hourly_price_cents=1000,
            limit=1,
        )
        assert [item.facility.name for item in recommendations] == ["Within budget"]

    asyncio.run(scenario())


def test_sql_facility_repository_maps_postgis_query_result() -> None:
    async def scenario() -> None:
        db = AsyncMock(spec=AsyncSession)
        row = ParkingFacilityRow(
            id=uuid4(),
            name="SQL garage",
            address="200 Database Drive",
            location="SRID=4326;POINT(-80.1918 25.7618)",
            hourly_price_cents=1000,
            safety_score=88,
            towing_incidents_per_1000=3,
            rating=4.2,
            available_spaces=10,
            capacity=50,
            navigation_url="https://maps.example.com/sql",
            provenance="official",
            confidence=0.9,
            observed_at=datetime.now(UTC),
            expires_at=None,
        )
        result = MagicMock()
        result.all.return_value = [(row, 125.4, 25.7618, -80.1918)]
        db.execute.return_value = result

        candidates = await SqlParkingFacilityRepository(db).nearby(
            -80.1918, 25.7617, 1500, 10
        )
        assert candidates[0].facility.name == "SQL garage"
        assert candidates[0].walking_distance_meters == 125.4
        db.execute.assert_awaited_once()

    asyncio.run(scenario())


def test_recommendation_http_contract_is_private_and_explainable() -> None:
    user = User(
        uuid4(), "driver@example.com", "hash", Role.USER, True, True, datetime.now(UTC)
    )
    service = ParkingRecommendationService(
        InMemoryParkingFacilityRepository((facility("Safe garage"),))
    )
    application = create_app()
    application.dependency_overrides[current_user] = lambda: user
    application.dependency_overrides[recommendation_service] = lambda: service
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/recommendations/nearby",
            json={
                "latitude": 25.7617,
                "longitude": -80.1918,
                "radius_meters": 1500,
                "limit": 5,
            },
        )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-store"
    option = response.json()["recommendations"][0]
    assert option["name"] == "Safe garage"
    assert option["provenance"] == "official"
    assert option["reasons"]
