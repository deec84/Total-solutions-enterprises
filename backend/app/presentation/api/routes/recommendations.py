"""Authenticated nearby parking recommendation API."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import database_session
from app.modules.identity.domain import User
from app.modules.recommendations.schemas import (
    ParkingRecommendationResponse,
    RecommendationListResponse,
    RecommendationRequest,
)
from app.modules.recommendations.service import ParkingRecommendationService
from app.modules.recommendations.sql_repository import SqlParkingFacilityRepository
from app.presentation.api.routes.auth import current_user

router = APIRouter()


def recommendation_service(
    session: Annotated[AsyncSession, Depends(database_session)],
) -> ParkingRecommendationService:
    return ParkingRecommendationService(SqlParkingFacilityRepository(session))


@router.post("/nearby", response_model=RecommendationListResponse)
async def nearby_recommendations(
    command: RecommendationRequest,
    _: Annotated[User, Depends(current_user)],
    service: Annotated[ParkingRecommendationService, Depends(recommendation_service)],
    response: Response,
) -> RecommendationListResponse:
    response.headers["Cache-Control"] = "private, no-store"
    recommendations = await service.nearby(
        command.longitude,
        command.latitude,
        command.radius_meters,
        command.max_hourly_price_cents,
        command.limit,
    )
    return RecommendationListResponse(
        recommendations=[
            ParkingRecommendationResponse(
                id=str(item.facility.id),
                name=item.facility.name,
                address=item.facility.address,
                latitude=item.facility.latitude,
                longitude=item.facility.longitude,
                walking_distance_meters=item.walking_distance_meters,
                hourly_price_cents=item.facility.hourly_price_cents,
                safety_score=item.facility.safety_score,
                towing_incidents_per_1000=item.facility.towing_incidents_per_1000,
                rating=item.facility.rating,
                available_spaces=item.facility.available_spaces,
                capacity=item.facility.capacity,
                navigation_url=item.facility.navigation_url,
                provenance=item.facility.provenance,
                confidence=item.facility.confidence,
                ranking_score=item.ranking_score,
                reasons=list(item.reasons),
            )
            for item in recommendations
        ],
        disclaimer=(
            "Availability, price, and restrictions can change. Confirm posted terms on arrival."
        ),
    )
