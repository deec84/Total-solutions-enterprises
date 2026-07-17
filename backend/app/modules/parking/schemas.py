"""Parking map HTTP contracts."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.parking.domain import Provenance, RiskLevel, ZoneType


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


class ParkingDecisionResponse(BaseModel):
    covered: bool
    message: str
    zone: ParkingZoneResponse | None = None
