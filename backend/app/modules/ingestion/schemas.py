"""Validated municipal ingestion HTTP contracts."""

from pydantic import BaseModel, Field

from app.modules.ingestion.domain import DataFormat, FeedKind, ImportStatus
from app.modules.parking.domain import Provenance


class MunicipalSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    jurisdiction: str = Field(min_length=1, max_length=160)
    feed_kind: FeedKind
    data_format: DataFormat
    source_url: str = Field(min_length=8, max_length=1000)
    license_url: str | None = Field(default=None, min_length=8, max_length=1000)
    official: bool = False
    refresh_interval_minutes: int = Field(default=1440, ge=5, le=10080)
    stale_after_minutes: int = Field(default=2880, ge=5, le=43200)


class MunicipalSourceResponse(BaseModel):
    id: str
    name: str
    jurisdiction: str
    feed_kind: FeedKind
    data_format: DataFormat
    source_url: str
    license_url: str | None
    official: bool
    provenance: Provenance
    enabled: bool
    refresh_interval_minutes: int
    stale_after_minutes: int
    created_at: str
    updated_at: str


class ImportBatchResponse(BaseModel):
    id: str
    source_id: str
    content_sha256: str
    importer_version: str
    status: ImportStatus
    input_count: int
    accepted_count: int
    rejected_count: int
    received_at: str
    completed_at: str
