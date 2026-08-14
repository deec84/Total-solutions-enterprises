"""Public, fail-closed parking-decision contract tests using synthetic evidence."""

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.identity.domain import Role, User
from app.modules.parking.domain import (
    CoverageStatus,
    ParkingDecisionOutcome,
    ParkingTemporalRule,
    ParkingZone,
    Provenance,
    TemporalRuleEffect,
    TemporalWindow,
    ZoneType,
)
from app.modules.parking.schemas import ParkingDecisionResponse
from app.modules.parking.service import ParkingDecisionService, ParkingMapService
from app.presentation.api.errors import ErrorCode
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.parking import parking_decision_service


class Zones:
    def __init__(self, zones: tuple[ParkingZone, ...] = ()) -> None:
        self._zones = zones

    async def in_viewport(
        self, west: float, south: float, east: float, north: float, limit: int
    ) -> tuple[ParkingZone, ...]:
        return self._zones

    async def at_location(
        self, longitude: float, latitude: float, *, include_expired: bool = False
    ) -> ParkingZone | None:
        now = datetime.now(UTC)
        candidates = (
            self._zones
            if include_expired
            else tuple(
                zone for zone in self._zones if zone.expires_at is None or zone.expires_at > now
            )
        )
        return candidates[0] if candidates else None


def zone(
    *,
    zone_type: ZoneType = ZoneType.GENERAL,
    score: int = 90,
    provenance: Provenance = Provenance.OFFICIAL,
    confidence: float = 1.0,
    towing_hotspot: bool = False,
    expires_at: datetime | None = None,
) -> ParkingZone:
    return ParkingZone(
        id=uuid4(),
        name="SYNTHETIC PARKING ZONE — NOT OFFICIAL",
        zone_type=zone_type,
        geometry_geojson='{"type":"Polygon","coordinates":[]}',
        parking_score=score,
        provenance=provenance,
        confidence=confidence,
        restriction_summary="Synthetic test restriction only.",
        average_towing_cost_cents=20_000,
        towing_hotspot=towing_hotspot,
        observed_at=datetime.now(UTC),
        expires_at=expires_at,
        source_id=uuid4(),
        import_batch_id=uuid4(),
    )


def service(*zones: ParkingZone) -> ParkingDecisionService:
    return ParkingDecisionService(ParkingMapService(Zones(tuple(zones))))


async def evaluate(value: ParkingDecisionService, **overrides: object):
    request = {
        "accuracy_meters": 10,
        "located_at": datetime.now(UTC),
        "location_consent": True,
    }
    request.update(overrides)
    if "now" in request and "located_at" not in overrides:
        request["located_at"] = request["now"]
    return await value.evaluate(
        -80.1918,
        25.7617,
        **request,
    )


def test_official_prohibition_and_towing_risk_are_do_not_park() -> None:
    private = asyncio.run(evaluate(service(zone(zone_type=ZoneType.PRIVATE_PROPERTY))))
    towing = asyncio.run(evaluate(service(zone(towing_hotspot=True))))
    assert private.outcome is ParkingDecisionOutcome.DO_NOT_PARK
    assert towing.outcome is ParkingDecisionOutcome.DO_NOT_PARK
    assert private.coverage_status is CoverageStatus.VERIFIED_COVERAGE


def test_resident_permit_and_current_official_evidence() -> None:
    without = asyncio.run(evaluate(service(zone(zone_type=ZoneType.RESIDENT_ONLY))))
    with_permit = asyncio.run(
        evaluate(service(zone(zone_type=ZoneType.RESIDENT_ONLY)), has_resident_permit=True)
    )
    assert without.outcome is ParkingDecisionOutcome.DO_NOT_PARK
    assert with_permit.outcome is ParkingDecisionOutcome.PARK
    assert with_permit.zone is not None and with_permit.zone.provenance is Provenance.OFFICIAL


def test_expired_temporary_evidence_and_unverified_evidence_fail_closed() -> None:
    expired = asyncio.run(
        evaluate(service(zone(expires_at=datetime.now(UTC) - timedelta(seconds=1))))
    )
    estimated = asyncio.run(evaluate(service(zone(provenance=Provenance.ESTIMATED))))
    assert expired.outcome is ParkingDecisionOutcome.INDETERMINATE
    assert expired.coverage_status is CoverageStatus.STALE_DATA
    assert estimated.outcome is ParkingDecisionOutcome.INDETERMINATE
    assert estimated.coverage_status is CoverageStatus.UNVERIFIABLE_SOURCE


def test_no_coverage_imprecise_or_old_location_is_indeterminate() -> None:
    no_coverage = asyncio.run(evaluate(service()))
    imprecise = asyncio.run(evaluate(service(zone()), accuracy_meters=21))
    old = asyncio.run(
        evaluate(service(zone()), located_at=datetime.now(UTC) - timedelta(minutes=3))
    )
    without_consent = asyncio.run(evaluate(service(zone()), location_consent=False))
    assert no_coverage.coverage_status is CoverageStatus.NO_VERIFIED_COVERAGE
    assert imprecise.coverage_status is CoverageStatus.LOCATION_PRECISION_INSUFFICIENT
    assert old.coverage_status is CoverageStatus.LOCATION_STALE
    assert without_consent.coverage_status is CoverageStatus.LOCATION_CONSENT_REQUIRED
    assert all(
        decision.outcome is ParkingDecisionOutcome.INDETERMINATE
        for decision in (no_coverage, imprecise, old, without_consent)
    )


def temporal_rule(
    effect: TemporalRuleEffect,
    *,
    weekdays: tuple[int, ...] = (0,),
    start: time = time(9),
    end: time = time(17),
    exceptions: tuple = (),
) -> ParkingTemporalRule:
    return ParkingTemporalRule(
        "synthetic-rule",
        effect,
        weekdays,
        TemporalWindow(start, end),
        "UTC",
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 2, 1, tzinfo=UTC),
        exceptions,
    )


def test_temporal_rules_cover_allowed_prohibited_exception_and_overlap() -> None:
    monday = datetime(2026, 1, 5, 10, tzinfo=UTC)
    allowed = replace(
        zone(),
        temporal_rules=(temporal_rule(TemporalRuleEffect.PARK),),
        temporal_schedule_required=True,
    )
    prohibited = replace(allowed, temporal_rules=(temporal_rule(TemporalRuleEffect.DO_NOT_PARK),))
    exception = replace(
        allowed,
        temporal_rules=(temporal_rule(TemporalRuleEffect.PARK, exceptions=(monday.date(),)),),
    )
    overlap = replace(
        allowed,
        temporal_rules=(
            temporal_rule(TemporalRuleEffect.PARK),
            temporal_rule(TemporalRuleEffect.DO_NOT_PARK),
        ),
    )
    assert asyncio.run(evaluate(service(allowed), now=monday)).outcome is (
        ParkingDecisionOutcome.PARK
    )
    assert asyncio.run(evaluate(service(prohibited), now=monday)).outcome is (
        ParkingDecisionOutcome.DO_NOT_PARK
    )
    assert asyncio.run(evaluate(service(exception), now=monday)).outcome is (
        ParkingDecisionOutcome.INDETERMINATE
    )
    assert asyncio.run(evaluate(service(overlap), now=monday)).outcome is (
        ParkingDecisionOutcome.DO_NOT_PARK
    )


def test_temporal_rules_fail_closed_for_missing_schedule_expiry_and_day_boundary() -> None:
    monday = datetime(2026, 1, 5, 23, 30, tzinfo=UTC)
    required = replace(zone(), temporal_schedule_required=True)
    overnight = replace(
        required,
        temporal_rules=(temporal_rule(TemporalRuleEffect.PARK, start=time(22), end=time(2)),),
    )
    expired = replace(
        required,
        temporal_rules=(
            ParkingTemporalRule(
                "expired",
                TemporalRuleEffect.PARK,
                (0,),
                TemporalWindow(time(9), time(17)),
                "UTC",
                datetime(2025, 1, 1, tzinfo=UTC),
                datetime(2025, 2, 1, tzinfo=UTC),
            ),
        ),
    )
    assert asyncio.run(evaluate(service(required), now=monday)).outcome is (
        ParkingDecisionOutcome.INDETERMINATE
    )
    assert (
        asyncio.run(evaluate(service(overnight), now=monday)).outcome is ParkingDecisionOutcome.PARK
    )
    assert asyncio.run(evaluate(service(expired), now=monday)).outcome is (
        ParkingDecisionOutcome.INDETERMINATE
    )


def test_http_contract_exposes_evidence_without_location_or_sensitive_data() -> None:
    application = create_app()
    application.dependency_overrides[current_user] = lambda: User(
        uuid4(), "driver@example.test", "hash", Role.USER, True, True, datetime.now(UTC)
    )
    application.dependency_overrides[parking_decision_service] = lambda: service(zone())
    with TestClient(application) as client:
        response = client.get(
            "/api/v1/parking/decision/evaluate",
            params={
                "latitude": 25.7617,
                "longitude": -80.1918,
                "accuracy_meters": 10,
                "located_at": datetime.now(UTC).isoformat(),
                "location_consent": True,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "PARK"
    assert payload["coverage_status"] == "VERIFIED_COVERAGE"
    assert payload["evidence"]["provenance"] == "official"
    assert payload["evidence"]["source_id"]
    assert payload["evidence"]["import_batch_id"]
    serialized = json.dumps(payload).lower()
    for forbidden in (
        "token",
        "password",
        "stack",
        "traceback",
        "select ",
        "latitude",
        "longitude",
    ):
        assert forbidden not in serialized


def test_decision_specific_codes_are_part_of_error_contract_v1_catalog() -> None:
    assert ErrorCode.NO_VERIFIED_COVERAGE.value == "NO_VERIFIED_COVERAGE"
    assert ErrorCode.STALE_DATA.value == "STALE_DATA"
    assert ErrorCode.LOCATION_PRECISION_INSUFFICIENT.value == "LOCATION_PRECISION_INSUFFICIENT"
    assert ErrorCode.DECISION_INDETERMINATE.value == "DECISION_INDETERMINATE"


def test_versioned_parking_fixtures_are_synthetic_and_match_the_public_contract() -> None:
    root = Path(__file__).resolve().parents[2] / "contracts" / "fixtures" / "parking"
    verified = json.loads((root / "verified-decision.v1.json").read_text())
    indeterminate = json.loads((root / "indeterminate-no-coverage.v1.json").read_text())
    assert ParkingDecisionResponse.model_validate(verified).outcome is ParkingDecisionOutcome.PARK
    assert (
        ParkingDecisionResponse.model_validate(indeterminate).outcome
        is ParkingDecisionOutcome.INDETERMINATE
    )
    assert "synthetic" in json.dumps(verified).lower()
