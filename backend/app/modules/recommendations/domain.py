"""Parking facility and explainable ranking contracts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.parking.domain import Provenance


@dataclass(frozen=True, slots=True)
class ParkingFacility:
    id: UUID
    name: str
    address: str
    latitude: float
    longitude: float
    hourly_price_cents: int | None
    safety_score: int
    towing_incidents_per_1000: float
    rating: float | None
    available_spaces: int | None
    capacity: int | None
    navigation_url: str
    provenance: Provenance
    confidence: float
    observed_at: datetime
    expires_at: datetime | None


@dataclass(frozen=True, slots=True)
class ParkingCandidate:
    facility: ParkingFacility
    walking_distance_meters: float


@dataclass(frozen=True, slots=True)
class ParkingRecommendation:
    facility: ParkingFacility
    walking_distance_meters: int
    ranking_score: int
    reasons: tuple[str, ...]


class ParkingFacilityRepository(Protocol):
    async def nearby(
        self, longitude: float, latitude: float, radius_meters: int, limit: int
    ) -> tuple[ParkingCandidate, ...]: ...
