from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.notifications.domain import DevicePlatform


class PreferenceUpdate(BaseModel):
    parking_alerts_enabled: bool
    background_location_enabled: bool
    push_enabled: bool
    quiet_start_hour: int = Field(ge=0, le=23)
    quiet_end_hour: int = Field(ge=0, le=23)
    timezone: str = Field(min_length=1, max_length=64)


class PreferenceResponse(PreferenceUpdate):
    updated_at: datetime


class DeviceRegistration(BaseModel):
    platform: DevicePlatform
    token: str = Field(min_length=20, max_length=4096)


class DeviceResponse(BaseModel):
    id: str
    platform: DevicePlatform
    enabled: bool


class LocationEvaluation(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class AlertDecisionResponse(BaseModel):
    should_alert: bool
    reason: str
    parking_score: int | None
    risk_level: str | None
    estimated_towing_cost_cents: int | None
    deduplicated: bool
