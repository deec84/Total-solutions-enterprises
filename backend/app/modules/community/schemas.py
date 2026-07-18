from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.community.domain import AppealStatus, ReportCategory, ReportStatus


class ReportCreate(BaseModel):
    category: ReportCategory
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    description: str = Field(min_length=12, max_length=1000)


class ModerationCommand(BaseModel):
    approved: bool
    reason: str = Field(min_length=5, max_length=500)


class AppealCreate(BaseModel):
    reason: str = Field(min_length=12, max_length=1000)


class AppealResolution(BaseModel):
    overturned: bool
    reason: str = Field(min_length=5, max_length=500)


class AppealResponse(BaseModel):
    id: UUID
    report_id: UUID
    appellant_id: UUID
    reason: str
    status: AppealStatus
    created_at: datetime
    resolved_at: datetime | None
    resolution_reason: str | None


class ReportResponse(BaseModel):
    id: UUID
    reporter_id: UUID
    category: ReportCategory
    latitude: float
    longitude: float
    description: str
    status: ReportStatus
    validation_score: float
    photo_sha256: str | None
    photo_available: bool
    photo_retained_until: datetime | None
    photo_deleted_at: datetime | None
    created_at: datetime
    expires_at: datetime
    moderation_reason: str | None


class MediaPurgeResponse(BaseModel):
    scanned: int
    deleted: int
    failed: int


class MediaAccessResponse(BaseModel):
    url: str
    expires_at: datetime
