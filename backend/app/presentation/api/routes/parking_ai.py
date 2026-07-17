"""Parking AI assistant HTTP adapter."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.modules.identity.domain import User
from app.modules.parking.service import ParkingMapService
from app.modules.parking_ai.domain import AssistantIntent, ParkingAssessment
from app.modules.parking_ai.intents import answer_for, interpret_intent
from app.modules.parking_ai.prediction import BaselinePredictionModel
from app.modules.parking_ai.rules import DeterministicParkingRules
from app.modules.parking_ai.schemas import ParkingAssistantRequest, ParkingAssistantResponse
from app.modules.parking_ai.service import ParkingAssistantService
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.parking import parking_map_service

router = APIRouter()


def parking_assistant_service(
    map_service: Annotated[ParkingMapService, Depends(parking_map_service)],
) -> ParkingAssistantService:
    return ParkingAssistantService(
        map_service, DeterministicParkingRules(), BaselinePredictionModel()
    )


@router.post("/parking-assistant", response_model=ParkingAssistantResponse)
async def parking_assistant(
    request: ParkingAssistantRequest,
    _: Annotated[User, Depends(current_user)],
    service: Annotated[ParkingAssistantService, Depends(parking_assistant_service)],
    response: Response,
) -> ParkingAssistantResponse:
    response.headers["Cache-Control"] = "no-store"
    assessment = await service.assess(
        request.longitude, request.latitude, request.has_resident_permit
    )
    return _response(assessment, interpret_intent(request.question))


def _response(
    assessment: ParkingAssessment, intent: AssistantIntent
) -> ParkingAssistantResponse:
    return ParkingAssistantResponse(
        answer=answer_for(intent, assessment),
        interpreted_intent=intent,
        parking_score=assessment.score,
        risk_level=assessment.risk_level,
        recommendation=assessment.recommendation,
        provenance=assessment.provenance,
        confidence=assessment.confidence,
        reasons=list(assessment.reasons),
        restriction_summary=assessment.restriction_summary,
        average_towing_cost_cents=assessment.average_towing_cost_cents,
        ruleset_version=assessment.ruleset_version,
        prediction_version=assessment.prediction_version,
        requires_human_review=assessment.requires_human_review,
        disclaimer=(
            "Parking rules can change. Always follow current official signs and instructions."
        ),
    )
