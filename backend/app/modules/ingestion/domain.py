"""Municipal source, normalization, batch, and repository contracts."""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.modules.parking.domain import Provenance, ZoneType


class FeedKind(StrEnum):
    PARKING_ZONES = "parking_zones"
    PARKING_FACILITIES = "parking_facilities"


class DataFormat(StrEnum):
    GEOJSON = "geojson"
    CSV = "csv"


class ImportStatus(StrEnum):
    COMMITTED = "committed"
    PARTIAL = "partial"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class MunicipalSource:
    id: UUID
    name: str
    jurisdiction: str
    feed_kind: FeedKind
    data_format: DataFormat
    source_url: str
    license_url: str | None
    official: bool
    enabled: bool
    refresh_interval_minutes: int
    stale_after_minutes: int
    created_at: datetime
    updated_at: datetime

    @property
    def provenance(self) -> Provenance:
        return Provenance.OFFICIAL if self.official else Provenance.ESTIMATED


@dataclass(frozen=True, slots=True)
class NormalizedParkingZone:
    external_id: str
    name: str
    zone_type: ZoneType
    geometry_geojson: str
    parking_score: int
    restriction_summary: str | None
    average_towing_cost_cents: int | None
    towing_hotspot: bool
    observed_at: datetime
    expires_at: datetime | None


@dataclass(frozen=True, slots=True)
class NormalizedParkingFacility:
    external_id: str
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
    observed_at: datetime
    expires_at: datetime | None


@dataclass(frozen=True, slots=True)
class RejectedRecord:
    record_index: int
    record_sha256: str
    reason_code: str
    reason_detail: str


@dataclass(frozen=True, slots=True)
class NormalizedImport:
    input_count: int
    zones: tuple[NormalizedParkingZone, ...] = ()
    facilities: tuple[NormalizedParkingFacility, ...] = ()
    rejected: tuple[RejectedRecord, ...] = ()

    @property
    def accepted_count(self) -> int:
        return len(self.zones) + len(self.facilities)


@dataclass(frozen=True, slots=True)
class ImportBatch:
    id: UUID
    source_id: UUID
    content_sha256: str
    importer_version: str
    status: ImportStatus
    input_count: int
    accepted_count: int
    rejected_count: int
    received_at: datetime
    completed_at: datetime


class MunicipalConnector(Protocol):
    @abstractmethod
    def parse(self, payload: bytes) -> NormalizedImport:
        """Validate and normalize untrusted feed bytes without network access."""


class MunicipalIngestionRepository(Protocol):
    @abstractmethod
    async def add_source(self, source: MunicipalSource) -> None:
        """Persist a validated source configuration."""

    @abstractmethod
    async def source(self, source_id: UUID) -> MunicipalSource | None:
        """Load one configured source."""

    @abstractmethod
    async def sources(self) -> tuple[MunicipalSource, ...]:
        """List configured sources in stable order."""

    @abstractmethod
    async def batch_by_digest(
        self, source_id: UUID, content_sha256: str
    ) -> ImportBatch | None:
        """Return an earlier batch for idempotent feed replay."""

    @abstractmethod
    async def commit_import(
        self,
        source: MunicipalSource,
        batch: ImportBatch,
        normalized: NormalizedImport,
    ) -> None:
        """Atomically persist batch evidence, quarantine, and accepted records."""

    @abstractmethod
    async def batches(self, source_id: UUID, limit: int) -> tuple[ImportBatch, ...]:
        """List recent import results for a source."""
