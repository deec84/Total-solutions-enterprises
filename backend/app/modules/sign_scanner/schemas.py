"""Sign scanner HTTP contracts."""

from pydantic import BaseModel, Field


class SignScanResponse(BaseModel):
    detected_text: str
    redacted_text: str
    language: str
    summary: str
    restrictions: list[str]
    towing_risk_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool
    provider_version: str
    disclaimer: str
