"""Governed lifecycle for transient community photo evidence."""

import hashlib
from abc import abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from app.modules.community.domain import CommunityReport, CommunityReportRepository

ALLOWED_MEDIA_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
MAX_MEDIA_BYTES = 10 * 1024 * 1024
MAX_RETENTION_DAYS = 30


class MediaStorageError(RuntimeError):
    """Stable application error for object-store failures."""


class MediaUnavailableError(ValueError):
    """Raised when governed evidence is absent, deleted, or expired."""


class CommunityMediaStore(Protocol):
    @abstractmethod
    async def put(
        self,
        *,
        key: str,
        payload: bytes,
        content_type: str,
        checksum_sha256: str,
        retained_until: datetime,
    ) -> None:
        """Store private evidence with integrity and retention metadata."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete private evidence by its internal object key."""

    @abstractmethod
    async def create_read_url(self, key: str, expires_seconds: int) -> str:
        """Create a short-lived private URL for privileged review."""


@dataclass(frozen=True, slots=True)
class StoredCommunityMedia:
    object_key: str
    content_type: str
    size_bytes: int
    retained_until: datetime


@dataclass(frozen=True, slots=True)
class MediaPurgeResult:
    scanned: int
    deleted: int
    failed: int


@dataclass(frozen=True, slots=True)
class MediaAccessGrant:
    url: str
    expires_at: datetime


class CommunityMediaLifecycle:
    """Store, delete, and expire evidence without exposing object identifiers."""

    def __init__(
        self,
        repository: CommunityReportRepository,
        store: CommunityMediaStore,
        retention_days: int = MAX_RETENTION_DAYS,
    ) -> None:
        if not 1 <= retention_days <= MAX_RETENTION_DAYS:
            raise ValueError("media retention must be between 1 and 30 days")
        self._repository = repository
        self._store = store
        self._retention = timedelta(days=retention_days)

    async def store(
        self,
        report_id: UUID,
        payload: bytes,
        content_type: str,
        checksum_sha256: str,
        now: datetime,
    ) -> StoredCommunityMedia:
        if content_type not in ALLOWED_MEDIA_TYPES:
            raise ValueError("unsupported community media type")
        if not payload or len(payload) > MAX_MEDIA_BYTES:
            raise ValueError("community media must contain at most 10 MB")
        if hashlib.sha256(payload).hexdigest() != checksum_sha256:
            raise ValueError("community media checksum mismatch")
        if now.tzinfo is None:
            raise ValueError("media timestamps must be timezone-aware")

        retained_until = now.astimezone(UTC) + self._retention
        object_key = f"community-reports/{report_id}/{checksum_sha256}"
        await self._store.put(
            key=object_key,
            payload=payload,
            content_type=content_type,
            checksum_sha256=checksum_sha256,
            retained_until=retained_until,
        )
        return StoredCommunityMedia(
            object_key=object_key,
            content_type=content_type,
            size_bytes=len(payload),
            retained_until=retained_until,
        )

    async def discard(self, object_key: str) -> None:
        await self._store.delete(object_key)

    async def delete_report_photo(
        self, report: CommunityReport, deleted_at: datetime | None = None
    ) -> CommunityReport:
        if not report.photo_available or report.photo_object_key is None:
            return report
        deletion_time = deleted_at or datetime.now(UTC)
        await self._store.delete(report.photo_object_key)
        updated = await self._repository.mark_photo_deleted(report.id, deletion_time)
        if updated is None:
            raise MediaStorageError("report disappeared while deleting photo evidence")
        return updated

    async def create_access_grant(
        self,
        report_id: UUID,
        now: datetime | None = None,
        expires_seconds: int = 60,
    ) -> MediaAccessGrant:
        if not 30 <= expires_seconds <= 300:
            raise ValueError("media access lifetime must be between 30 and 300 seconds")
        requested_at = now or datetime.now(UTC)
        report = await self._repository.get(report_id)
        if (
            report is None
            or not report.photo_available
            or report.photo_object_key is None
            or report.photo_retained_until is None
            or report.photo_retained_until <= requested_at
        ):
            raise MediaUnavailableError("community photo evidence is unavailable")
        url = await self._store.create_read_url(
            report.photo_object_key, expires_seconds=expires_seconds
        )
        return MediaAccessGrant(url, requested_at + timedelta(seconds=expires_seconds))

    async def purge_expired(
        self, now: datetime | None = None, limit: int = 100
    ) -> MediaPurgeResult:
        if not 1 <= limit <= 500:
            raise ValueError("media purge limit must be between 1 and 500")
        cutoff = now or datetime.now(UTC)
        reports = await self._repository.expired_media(cutoff, limit)
        deleted = 0
        failed = 0
        for report in reports:
            try:
                await self.delete_report_photo(report, cutoff)
            except MediaStorageError:
                failed += 1
            else:
                deleted += 1
        return MediaPurgeResult(len(reports), deleted, failed)
