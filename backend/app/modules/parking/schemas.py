"""Parking map HTTP contracts."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.parking.domain import (
    CoverageStatus,
    ParkingDecisionOutcome,
    ParkingDecisionReasonCode,
    Provenance,
    RiskLevel,
    ZoneType,
)


class ParkingZoneResponse(BaseModel):
    id: str
    name: str
    zone_type: ZoneType
    geometry: dict[str, Any]
    parking_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    provenance: Provenance
    confidence: float = Field(ge=0, le=1)
    restriction_summary: str | None
    average_towing_cost_cents: int | None = Field(default=None, ge=0)
    towing_hotspot: bool
    observed_at: datetime
    expires_at: datetime | None


class ParkingViewportResponse(BaseModel):
    zones: list[ParkingZoneResponse]


class ParkingDecisionReasonResponse(BaseModel):
    code: ParkingDecisionReasonCode
    message: str = Field(min_length=1, max_length=160)


class ParkingDecisionEvidenceResponse(BaseModel):
    zone_id: str
    zone_type: ZoneType
    provenance: Provenance
    confidence: float = Field(ge=0, le=1)
    observed_at: datetime
    expires_at: datetime | None
    source_id: str | None = None
    import_batch_id: str | None = None
    restriction_summary: str | None


class ParkingDecisionResponse(BaseModel):
    outcome: ParkingDecisionOutcome
    coverage_status: CoverageStatus
    reasons: list[ParkingDecisionReasonResponse] = Field(min_length=1, max_length=8)
    evidence: ParkingDecisionEvidenceResponse | None = None
    evaluated_at: datetime


class LegacyParkingDecisionResponse(BaseModel):
    """Deprecated map response retained while Flutter remains a transition reference."""

    covered: bool
    message: str
    zone: ParkingZoneResponse | None = None
