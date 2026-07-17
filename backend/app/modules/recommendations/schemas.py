"""Nearby parking recommendation API contracts."""

from pydantic import BaseModel, Field

from app.modules.parking.domain import Provenance


class RecommendationRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_meters: int = Field(default=1500, ge=100, le=5000)
    max_hourly_price_cents: int | None = Field(default=None, ge=0, le=100_000)
    limit: int = Field(default=10, ge=1, le=20)


class ParkingRecommendationResponse(BaseModel):
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    walking_distance_meters: int
    hourly_price_cents: int | None
    safety_score: int = Field(ge=0, le=100)
    towing_incidents_per_1000: float = Field(ge=0)
    rating: float | None = Field(default=None, ge=0, le=5)
    available_spaces: int | None
    capacity: int | None
    navigation_url: str
    provenance: Provenance
    confidence: float = Field(ge=0, le=1)
    ranking_score: int = Field(ge=0, le=100)
    reasons: list[str]


class RecommendationListResponse(BaseModel):
    recommendations: list[ParkingRecommendationResponse]
    disclaimer: str
