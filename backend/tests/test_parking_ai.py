"""Safety precedence, versioning, and parking-assistant API tests."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.identity.domain import Role, User
from app.modules.parking.domain import ParkingZone, Provenance, ZoneType
from app.modules.parking.service import ParkingMapService
from app.modules.parking_ai.domain import AssistantIntent, Recommendation
from app.modules.parking_ai.intents import answer_for, interpret_intent
from app.modules.parking_ai.prediction import BaselinePredictionModel
from app.modules.parking_ai.rules import RULESET_VERSION, DeterministicParkingRules
from app.modules.parking_ai.service import ParkingAssistantService
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.parking_ai import parking_assistant_service


class ZoneRepository:
    def __init__(self, zone: ParkingZone | None) -> None:
        self.zone = zone

    async def in_viewport(
        self, west: float, south: float, east: float, north: float, limit: int
    ) -> tuple[ParkingZone, ...]:
        return (self.zone,) if self.zone is not None else ()

    async def at_location(self, longitude: float, latitude: float) -> ParkingZone | None:
        return self.zone


def zone(
    zone_type: ZoneType = ZoneType.GENERAL,
    score: int = 85,
    towing_hotspot: bool = False,
) -> ParkingZone:
    return ParkingZone(
        uuid4(),
        "Verified zone",
        zone_type,
        '{"type":"Polygon","coordinates":[]}',
        score,
        Provenance.OFFICIAL,
        1.0,
        "Official parking restriction summary",
        22500,
        towing_hotspot,
        datetime.now(UTC),
        None,
    )


def service(value: ParkingZone | None) -> ParkingAssistantService:
    return ParkingAssistantService(
        ParkingMapService(ZoneRepository(value)),
        DeterministicParkingRules(),
        BaselinePredictionModel(),
    )


def test_private_property_is_an_official_hard_stop() -> None:
    assessment = asyncio.run(service(zone(ZoneType.PRIVATE_PROPERTY, 95)).assess(-80, 25))
    assert assessment.score == 0
    assert assessment.recommendation is Recommendation.DO_NOT_PARK
    assert assessment.provenance is Provenance.OFFICIAL
    assert assessment.prediction_version is None
    assert assessment.requires_human_review is False


def test_resident_rule_requires_permit_then_preserves_verified_score() -> None:
    resident_service = service(zone(ZoneType.RESIDENT_ONLY, 80))
    without_permit = asyncio.run(resident_service.assess(-80, 25))
    with_permit = asyncio.run(
        resident_service.assess(-80, 25, has_resident_permit=True)
    )
    assert without_permit.score == 10
    assert with_permit.score == 80
    assert with_permit.recommendation is Recommendation.PARK


def test_towing_hotspot_caps_verified_score() -> None:
    assessment = asyncio.run(service(zone(score=90, towing_hotspot=True)).assess(-80, 25))
    assert assessment.score == 20
    assert "towing hotspot" in assessment.reasons[-1]


def test_missing_verified_data_uses_versioned_conservative_prediction() -> None:
    assessment = asyncio.run(service(None).assess(-80, 25))
    assert assessment.score == 50
    assert assessment.provenance is Provenance.AI_PREDICTION
    assert assessment.confidence == 0.35
    assert assessment.ruleset_version == RULESET_VERSION
    assert assessment.prediction_version == "parking-baseline-1.0.0"
    assert assessment.requires_human_review is True


def test_assistant_api_exposes_explanation_and_no_store() -> None:
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
    application.dependency_overrides[parking_assistant_service] = lambda: service(
        zone(ZoneType.PRIVATE_PROPERTY, 95)
    )
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/ai/parking-assistant",
            json={
                "question": "Can I park here?",
                "latitude": 25.76,
                "longitude": -80.19,
                "has_resident_permit": False,
            },
        )

    assert response.status_code == 200
    assert response.json()["recommendation"] == "do_not_park"
    assert response.json()["interpreted_intent"] == "parking_legality"
    assert response.json()["provenance"] == "official"
    assert response.json()["reasons"]
    assert response.json()["requires_human_review"] is False
    assert response.headers["Cache-Control"] == "no-store"


def test_assistant_interprets_supported_questions_without_inventing_evidence() -> None:
    assessment = asyncio.run(service(zone()).assess(-80, 25))
    assert interpret_intent("What is the estimated towing cost?") is AssistantIntent.TOWING_COST
    assert "$225.00" in answer_for(AssistantIntent.TOWING_COST, assessment)
    assert interpret_intent("What does this sign mean?") is AssistantIntent.SIGN_MEANING
    assert answer_for(AssistantIntent.SIGN_MEANING, assessment) == (
        "Official parking restriction summary"
    )
    assert interpret_intent("Where is the nearest safe parking?") is (
        AssistantIntent.NEAREST_SAFE_PARKING
    )
