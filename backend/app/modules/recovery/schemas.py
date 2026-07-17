"""Towing recovery API contracts."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.parking.domain import Provenance


class TowLookupRequest(BaseModel):
    state: str = Field(min_length=2, max_length=2)
    license_plate: str = Field(min_length=2, max_length=16)
    vin_last_six: str | None = Field(default=None, min_length=6, max_length=6)

    @field_validator("state", "license_plate", "vin_last_six")
    @classmethod
    def trim_identifiers(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class TowRecordResponse(BaseModel):
    tow_company: str
    storage_location: str
    phone_number: str
    business_hours: str
    required_documents: list[str]
    estimated_fees_cents: int | None
    payment_methods: list[str]
    navigation_url: str
    provenance: Provenance
    confidence: float = Field(ge=0, le=1)
    last_verified_at: datetime


class TowLookupResponse(BaseModel):
    found: bool
    message: str
    record: TowRecordResponse | None
    privacy_notice: str
