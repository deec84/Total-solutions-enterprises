"""Interactive parking-map HTTP adapter."""

import json
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import database_session
from app.modules.identity.domain import User
from app.modules.parking.domain import ParkingZone
from app.modules.parking.schemas import (
    LegacyParkingDecisionResponse,
    ParkingDecisionEvidenceResponse,
    ParkingDecisionReasonResponse,
    ParkingDecisionResponse,
    ParkingViewportResponse,
    ParkingZoneResponse,
)
from app.modules.parking.service import (
    InvalidViewportError,
    ParkingDecision,
    ParkingDecisionService,
    ParkingMapService,
)
from app.modules.parking.sql_repository import SqlParkingZoneRepository
from app.presentation.api.routes.auth import current_user

router = APIRouter()


def zone_response(zone: ParkingZone) -> ParkingZoneResponse:
    return ParkingZoneResponse(
        id=str(zone.id),
        name=zone.name,
        zone_type=zone.zone_type,
        geometry=json.loads(zone.geometry_geojson),
        parking_score=zone.parking_score,
        risk_level=zone.risk_level,
        provenance=zone.provenance,
        confidence=zone.confidence,
        restriction_summary=zone.restriction_summary,
        average_towing_cost_cents=zone.average_towing_cost_cents,
        towing_hotspot=zone.towing_hotspot,
        observed_at=zone.observed_at,
        expires_at=zone.expires_at,
    )


def parking_map_service(
    session: Annotated[AsyncSession, Depends(database_session)],
) -> ParkingMapService:
    return ParkingMapService(SqlParkingZoneRepository(session))


def parking_decision_service(
    map_service: Annotated[ParkingMapService, Depends(parking_map_service)],
) -> ParkingDecisionService:
    return ParkingDecisionService(map_service)


@router.get("/zones", response_model=ParkingViewportResponse)
async def viewport(
    _: Annotated[User, Depends(current_user)],
    service: Annotated[ParkingMapService, Depends(parking_map_service)],
    response: Response,
    west: Annotated[float, Query(ge=-180, le=180)],
    south: Annotated[float, Query(ge=-90, le=90)],
    east: Annotated[float, Query(ge=-180, le=180)],
    north: Annotated[float, Query(ge=-90, le=90)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
) -> ParkingViewportResponse:
    response.headers["Cache-Control"] = "private, max-age=30, stale-while-revalidate=60"
    response.headers["Vary"] = "Authorization"
    try:
        zones = await service.viewport(west, south, east, north, limit)
    except InvalidViewportError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return ParkingViewportResponse(
        zones=[zone_response(zone) for zone in zones]
    )


@router.get("/decision", response_model=LegacyParkingDecisionResponse, deprecated=True)
async def legacy_parking_decision(
    _: Annotated[User, Depends(current_user)],
    service: Annotated[ParkingMapService, Depends(parking_map_service)],
    response: Response,
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
) -> LegacyParkingDecisionResponse:
    response.headers["Cache-Control"] = "no-store"
    zone = await service.decision(longitude, latitude)
    if zone is None:
        return LegacyParkingDecisionResponse(
            covered=False,
            message="No verified parking intelligence covers this location. Read all signs.",
        )
    return LegacyParkingDecisionResponse(
        covered=True,
        message="Parking intelligence found for this location.",
        zone=zone_response(zone),
    )


@router.get("/decision/evaluate", response_model=ParkingDecisionResponse)
async def evaluate_parking_decision(
    _: Annotated[User, Depends(current_user)],
    service: Annotated[ParkingDecisionService, Depends(parking_decision_service)],
    response: Response,
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    accuracy_meters: Annotated[float, Query(ge=0, le=10_000)],
    located_at: datetime,
    location_consent: bool,
    has_resident_permit: bool = False,
) -> ParkingDecisionResponse:
    response.headers["Cache-Control"] = "no-store"
    decision = await service.evaluate(
        longitude,
        latitude,
        accuracy_meters=accuracy_meters,
        located_at=located_at,
        location_consent=location_consent,
        has_resident_permit=has_resident_permit,
    )
    return decision_response(decision)


def decision_response(decision: ParkingDecision) -> ParkingDecisionResponse:
    zone = decision.zone
    evidence = None
    if zone is not None:
        evidence = ParkingDecisionEvidenceResponse(
            zone_id=str(zone.id),
            zone_type=zone.zone_type,
            provenance=zone.provenance,
            confidence=zone.confidence,
            observed_at=zone.observed_at,
            expires_at=zone.expires_at,
            source_id=str(zone.source_id) if zone.source_id else None,
            import_batch_id=str(zone.import_batch_id) if zone.import_batch_id else None,
            restriction_summary=zone.restriction_summary,
        )
    return ParkingDecisionResponse(
        outcome=decision.outcome,
        coverage_status=decision.coverage_status,
        reasons=[
            ParkingDecisionReasonResponse(code=reason.code, message=reason.message)
            for reason in decision.reasons
        ],
        evidence=evidence,
        evaluated_at=decision.evaluated_at,
    )
