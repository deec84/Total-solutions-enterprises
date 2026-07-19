"""Concurrency-safe in-memory municipal ingestion adapter."""

import asyncio
from uuid import UUID

from app.modules.ingestion.domain import (
    ImportBatch,
    MunicipalSource,
    NormalizedImport,
)


class InMemoryMunicipalIngestionRepository:
    def __init__(self) -> None:
        self._sources: dict[UUID, MunicipalSource] = {}
        self._batches: dict[UUID, ImportBatch] = {}
        self._normalized: dict[UUID, NormalizedImport] = {}
        self._lock = asyncio.Lock()

    async def add_source(self, source: MunicipalSource) -> None:
        async with self._lock:
            self._sources[source.id] = source

    async def source(self, source_id: UUID) -> MunicipalSource | None:
        return self._sources.get(source_id)

    async def sources(self) -> tuple[MunicipalSource, ...]:
        return tuple(sorted(self._sources.values(), key=lambda item: (item.name, item.id)))

    async def batch_by_digest(
        self, source_id: UUID, content_sha256: str
    ) -> ImportBatch | None:
        return next(
            (
                item
                for item in self._batches.values()
                if item.source_id == source_id and item.content_sha256 == content_sha256
            ),
            None,
        )

    async def commit_import(
        self,
        source: MunicipalSource,
        batch: ImportBatch,
        normalized: NormalizedImport,
    ) -> None:
        async with self._lock:
            self._batches[batch.id] = batch
            self._normalized[batch.id] = normalized

    async def batches(self, source_id: UUID, limit: int) -> tuple[ImportBatch, ...]:
        matches = sorted(
            (item for item in self._batches.values() if item.source_id == source_id),
            key=lambda item: item.received_at,
            reverse=True,
        )
        return tuple(matches[:limit])

    def normalized(self, batch_id: UUID) -> NormalizedImport:
        return self._normalized[batch_id]
