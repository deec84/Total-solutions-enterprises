"""Parking assistant API contracts."""

from pydantic import BaseModel, Field

from app.modules.parking.domain import Provenance, RiskLevel
from app.modules.parking_ai.domain import AssistantIntent, Recommendation


class ParkingAssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    has_resident_permit: bool = False


class ParkingAssistantResponse(BaseModel):
    answer: str
    interpreted_intent: AssistantIntent
    parking_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    recommendation: Recommendation
    provenance: Provenance
    confidence: float = Field(ge=0, le=1)
    reasons: list[str]
    restriction_summary: str | None
    average_towing_cost_cents: int | None
    ruleset_version: str
    prediction_version: str | None
    requires_human_review: bool
    disclaimer: str
