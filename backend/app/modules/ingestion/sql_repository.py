"""PostgreSQL/PostGIS adapter for governed municipal imports."""

from uuid import UUID, uuid4, uuid5

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import (
    MunicipalImportBatchRow,
    MunicipalQuarantineRow,
    MunicipalSourceRow,
    ParkingFacilityRow,
    ParkingZoneRow,
)
from app.modules.ingestion.domain import (
    DataFormat,
    FeedKind,
    ImportBatch,
    ImportStatus,
    MunicipalSource,
    NormalizedImport,
)


def _source(row: MunicipalSourceRow) -> MunicipalSource:
    return MunicipalSource(
        row.id,
        row.name,
        row.jurisdiction,
        FeedKind(row.feed_kind),
        DataFormat(row.data_format),
        row.source_url,
        row.license_url,
        row.official,
        row.enabled,
        row.refresh_interval_minutes,
        row.stale_after_minutes,
        row.created_at,
        row.updated_at,
    )


def _batch(row: MunicipalImportBatchRow) -> ImportBatch:
    return ImportBatch(
        row.id,
        row.source_id,
        row.content_sha256,
        row.importer_version,
        ImportStatus(row.status),
        row.input_count,
        row.accepted_count,
        row.rejected_count,
        row.received_at,
        row.completed_at,
    )


class SqlMunicipalIngestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_source(self, source: MunicipalSource) -> None:
        self._session.add(
            MunicipalSourceRow(
                id=source.id,
                name=source.name,
                jurisdiction=source.jurisdiction,
                feed_kind=source.feed_kind.value,
                data_format=source.data_format.value,
                source_url=source.source_url,
                license_url=source.license_url,
                official=source.official,
                enabled=source.enabled,
                refresh_interval_minutes=source.refresh_interval_minutes,
                stale_after_minutes=source.stale_after_minutes,
                created_at=source.created_at,
                updated_at=source.updated_at,
            )
        )
        await self._session.flush()

    async def source(self, source_id: UUID) -> MunicipalSource | None:
        row = await self._session.get(MunicipalSourceRow, source_id)
        return _source(row) if row is not None else None

    async def sources(self) -> tuple[MunicipalSource, ...]:
        rows = await self._session.scalars(
            select(MunicipalSourceRow).order_by(MunicipalSourceRow.name, MunicipalSourceRow.id)
        )
        return tuple(_source(row) for row in rows)

    async def batch_by_digest(
        self, source_id: UUID, content_sha256: str
    ) -> ImportBatch | None:
        row = await self._session.scalar(
            select(MunicipalImportBatchRow).where(
                MunicipalImportBatchRow.source_id == source_id,
                MunicipalImportBatchRow.content_sha256 == content_sha256,
            )
        )
        return _batch(row) if row is not None else None

    async def commit_import(
        self,
        source: MunicipalSource,
        batch: ImportBatch,
        normalized: NormalizedImport,
    ) -> None:
        self._session.add(
            MunicipalImportBatchRow(
                id=batch.id,
                source_id=batch.source_id,
                content_sha256=batch.content_sha256,
                importer_version=batch.importer_version,
                status=batch.status.value,
                input_count=batch.input_count,
                accepted_count=batch.accepted_count,
                rejected_count=batch.rejected_count,
                received_at=batch.received_at,
                completed_at=batch.completed_at,
            )
        )
        for item in normalized.rejected:
            self._session.add(
                MunicipalQuarantineRow(
                    id=uuid4(),
                    batch_id=batch.id,
                    record_index=item.record_index,
                    record_sha256=item.record_sha256,
                    reason_code=item.reason_code,
                    reason_detail=item.reason_detail,
                    created_at=batch.completed_at,
                )
            )
        await self._session.flush()
        for zone in normalized.zones:
            values = {
                "id": uuid5(source.id, zone.external_id),
                "name": zone.name,
                "zone_type": zone.zone_type.value,
                "geometry": func.ST_SetSRID(
                    func.ST_GeomFromGeoJSON(zone.geometry_geojson), 4326
                ),
                "parking_score": zone.parking_score,
                "provenance": source.provenance.value,
                "confidence": 1.0 if source.official else 0.5,
                "restriction_summary": zone.restriction_summary,
                "average_towing_cost_cents": zone.average_towing_cost_cents,
                "towing_hotspot": zone.towing_hotspot,
                "observed_at": zone.observed_at,
                "expires_at": zone.expires_at,
                "source_id": source.id,
                "import_batch_id": batch.id,
                "external_record_id": zone.external_id,
            }
            statement = insert(ParkingZoneRow).values(**values)
            await self._session.execute(
                statement.on_conflict_do_update(
                    index_elements=[
                        ParkingZoneRow.source_id,
                        ParkingZoneRow.external_record_id,
                    ],
                    set_={key: value for key, value in values.items() if key != "id"},
                )
            )
        for facility in normalized.facilities:
            values = {
                "id": uuid5(source.id, facility.external_id),
                "name": facility.name,
                "address": facility.address,
                "location": func.ST_SetSRID(
                    func.ST_MakePoint(facility.longitude, facility.latitude), 4326
                ),
                "hourly_price_cents": facility.hourly_price_cents,
                "safety_score": facility.safety_score,
                "towing_incidents_per_1000": facility.towing_incidents_per_1000,
                "rating": facility.rating,
                "available_spaces": facility.available_spaces,
                "capacity": facility.capacity,
                "navigation_url": facility.navigation_url,
                "provenance": source.provenance.value,
                "confidence": 1.0 if source.official else 0.5,
                "observed_at": facility.observed_at,
                "expires_at": facility.expires_at,
                "source_id": source.id,
                "import_batch_id": batch.id,
                "external_record_id": facility.external_id,
            }
            statement = insert(ParkingFacilityRow).values(**values)
            await self._session.execute(
                statement.on_conflict_do_update(
                    index_elements=[
                        ParkingFacilityRow.source_id,
                        ParkingFacilityRow.external_record_id,
                    ],
                    set_={key: value for key, value in values.items() if key != "id"},
                )
            )

    async def batches(self, source_id: UUID, limit: int) -> tuple[ImportBatch, ...]:
        rows = await self._session.scalars(
            select(MunicipalImportBatchRow)
            .where(MunicipalImportBatchRow.source_id == source_id)
            .order_by(MunicipalImportBatchRow.received_at.desc())
            .limit(limit)
        )
        return tuple(_batch(row) for row in rows)
