"""Municipal source governance and idempotent import orchestration."""

import hashlib
from datetime import UTC, datetime
from urllib.parse import urlparse
from uuid import UUID, uuid4

from app.modules.ingestion.connectors import IMPORTER_VERSION
from app.modules.ingestion.domain import (
    DataFormat,
    FeedKind,
    ImportBatch,
    ImportStatus,
    MunicipalConnector,
    MunicipalIngestionRepository,
    MunicipalSource,
)


class MunicipalIngestionError(ValueError):
    """Stable validation error for source and import requests."""


class MunicipalIngestionService:
    def __init__(
        self,
        repository: MunicipalIngestionRepository,
        connectors: dict[tuple[FeedKind, DataFormat], MunicipalConnector],
        max_upload_bytes: int,
    ) -> None:
        self._repository = repository
        self._connectors = connectors
        self._max_upload_bytes = max_upload_bytes

    async def create_source(
        self,
        *,
        name: str,
        jurisdiction: str,
        feed_kind: FeedKind,
        data_format: DataFormat,
        source_url: str,
        license_url: str | None,
        official: bool,
        refresh_interval_minutes: int,
        stale_after_minutes: int,
    ) -> MunicipalSource:
        if (feed_kind, data_format) not in self._connectors:
            raise MunicipalIngestionError("no approved connector supports this feed contract")
        self._validate_url(source_url, "source_url")
        if license_url is not None:
            self._validate_url(license_url, "license_url")
        if official and license_url is None:
            raise MunicipalIngestionError("official sources require a public license URL")
        if not 5 <= refresh_interval_minutes <= 10_080:
            raise MunicipalIngestionError("refresh interval must be between 5 and 10080 minutes")
        if stale_after_minutes < refresh_interval_minutes:
            raise MunicipalIngestionError("stale threshold cannot precede the refresh interval")
        normalized_name = name.strip()
        normalized_jurisdiction = jurisdiction.strip()
        if not normalized_name or len(normalized_name) > 160:
            raise MunicipalIngestionError("source name must contain at most 160 characters")
        if not normalized_jurisdiction or len(normalized_jurisdiction) > 160:
            raise MunicipalIngestionError("jurisdiction must contain at most 160 characters")
        now = datetime.now(UTC)
        source = MunicipalSource(
            uuid4(),
            normalized_name,
            normalized_jurisdiction,
            feed_kind,
            data_format,
            source_url,
            license_url,
            official,
            True,
            refresh_interval_minutes,
            stale_after_minutes,
            now,
            now,
        )
        await self._repository.add_source(source)
        return source

    async def sources(self) -> tuple[MunicipalSource, ...]:
        return await self._repository.sources()

    async def import_payload(self, source_id: UUID, payload: bytes) -> ImportBatch:
        if not payload or len(payload) > self._max_upload_bytes:
            raise MunicipalIngestionError(
                f"feed must contain between 1 and {self._max_upload_bytes} bytes"
            )
        source = await self._repository.source(source_id)
        if source is None:
            raise MunicipalIngestionError("municipal source not found")
        if not source.enabled:
            raise MunicipalIngestionError("municipal source is disabled")
        digest = hashlib.sha256(payload).hexdigest()
        existing = await self._repository.batch_by_digest(source_id, digest)
        if existing is not None:
            return existing
        connector = self._connectors.get((source.feed_kind, source.data_format))
        if connector is None:
            raise MunicipalIngestionError("configured connector is unavailable")
        received_at = datetime.now(UTC)
        normalized = connector.parse(payload)
        if normalized.accepted_count == 0:
            status = ImportStatus.REJECTED
        elif normalized.rejected:
            status = ImportStatus.PARTIAL
        else:
            status = ImportStatus.COMMITTED
        batch = ImportBatch(
            uuid4(),
            source.id,
            digest,
            IMPORTER_VERSION,
            status,
            normalized.input_count,
            normalized.accepted_count,
            len(normalized.rejected),
            received_at,
            datetime.now(UTC),
        )
        await self._repository.commit_import(source, batch, normalized)
        return batch

    async def batches(self, source_id: UUID, limit: int) -> tuple[ImportBatch, ...]:
        if await self._repository.source(source_id) is None:
            raise MunicipalIngestionError("municipal source not found")
        return await self._repository.batches(source_id, limit)

    @staticmethod
    def _validate_url(value: str, field: str) -> None:
        parsed = urlparse(value)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise MunicipalIngestionError(
                f"{field} must be an absolute HTTPS URL without credentials, queries, or fragments"
            )
