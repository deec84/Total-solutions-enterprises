"""MFA-protected municipal source and feed ingestion API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import database_session
from app.modules.admin.sql_audit import SqlAdminAuditTrail
from app.modules.identity.domain import User
from app.modules.ingestion.connectors import (
    CsvParkingFacilityConnector,
    GeoJsonParkingZoneConnector,
)
from app.modules.ingestion.domain import (
    DataFormat,
    FeedKind,
    ImportBatch,
    MunicipalSource,
)
from app.modules.ingestion.schemas import (
    ImportBatchResponse,
    MunicipalSourceCreate,
    MunicipalSourceResponse,
)
from app.modules.ingestion.service import (
    MunicipalIngestionError,
    MunicipalIngestionService,
)
from app.modules.ingestion.sql_repository import SqlMunicipalIngestionRepository
from app.presentation.api.routes.admin import privileged_user
from app.shared.config import get_settings

router = APIRouter()


def municipal_ingestion_service(
    session: Annotated[AsyncSession, Depends(database_session)],
) -> MunicipalIngestionService:
    settings = get_settings()
    if not settings.municipal_imports_enabled:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "municipal imports are disabled pending approved source rights",
        )
    return MunicipalIngestionService(
        SqlMunicipalIngestionRepository(session),
        {
            (FeedKind.PARKING_ZONES, DataFormat.GEOJSON): GeoJsonParkingZoneConnector(),
            (FeedKind.PARKING_FACILITIES, DataFormat.CSV): CsvParkingFacilityConnector(),
        },
        settings.municipal_max_upload_bytes,
    )


def ingestion_audit(
    session: Annotated[AsyncSession, Depends(database_session)],
) -> SqlAdminAuditTrail:
    return SqlAdminAuditTrail(session)


def source_response(source: MunicipalSource) -> MunicipalSourceResponse:
    return MunicipalSourceResponse(
        id=str(source.id),
        name=source.name,
        jurisdiction=source.jurisdiction,
        feed_kind=source.feed_kind,
        data_format=source.data_format,
        source_url=source.source_url,
        license_url=source.license_url,
        official=source.official,
        provenance=source.provenance,
        enabled=source.enabled,
        refresh_interval_minutes=source.refresh_interval_minutes,
        stale_after_minutes=source.stale_after_minutes,
        created_at=source.created_at.isoformat(),
        updated_at=source.updated_at.isoformat(),
    )


def batch_response(batch: ImportBatch) -> ImportBatchResponse:
    return ImportBatchResponse(
        id=str(batch.id),
        source_id=str(batch.source_id),
        content_sha256=batch.content_sha256,
        importer_version=batch.importer_version,
        status=batch.status,
        input_count=batch.input_count,
        accepted_count=batch.accepted_count,
        rejected_count=batch.rejected_count,
        received_at=batch.received_at.isoformat(),
        completed_at=batch.completed_at.isoformat(),
    )


@router.post("/sources", response_model=MunicipalSourceResponse, status_code=201)
async def create_source(
    command: MunicipalSourceCreate,
    actor: Annotated[User, Depends(privileged_user)],
    service: Annotated[MunicipalIngestionService, Depends(municipal_ingestion_service)],
    audit: Annotated[SqlAdminAuditTrail, Depends(ingestion_audit)],
) -> MunicipalSourceResponse:
    try:
        source = await service.create_source(**command.model_dump())
    except MunicipalIngestionError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    await audit.append(actor.id, "municipal.source_created", source.id)
    return source_response(source)


@router.get("/sources", response_model=list[MunicipalSourceResponse])
async def sources(
    _: Annotated[User, Depends(privileged_user)],
    service: Annotated[MunicipalIngestionService, Depends(municipal_ingestion_service)],
) -> list[MunicipalSourceResponse]:
    return [source_response(item) for item in await service.sources()]


@router.post("/sources/{source_id}/imports", response_model=ImportBatchResponse)
async def import_feed(
    source_id: UUID,
    actor: Annotated[User, Depends(privileged_user)],
    service: Annotated[MunicipalIngestionService, Depends(municipal_ingestion_service)],
    audit: Annotated[SqlAdminAuditTrail, Depends(ingestion_audit)],
    payload: Annotated[UploadFile, File()],
) -> ImportBatchResponse:
    maximum = get_settings().municipal_max_upload_bytes
    content = await payload.read(maximum + 1)
    try:
        batch = await service.import_payload(source_id, content)
    except MunicipalIngestionError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    await audit.append(actor.id, f"municipal.import_{batch.status.value}", batch.id)
    return batch_response(batch)


@router.get("/sources/{source_id}/imports", response_model=list[ImportBatchResponse])
async def batches(
    source_id: UUID,
    _: Annotated[User, Depends(privileged_user)],
    service: Annotated[MunicipalIngestionService, Depends(municipal_ingestion_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[ImportBatchResponse]:
    try:
        items = await service.batches(source_id, limit)
    except MunicipalIngestionError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return [batch_response(item) for item in items]
