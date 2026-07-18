"""Community submission and moderation endpoints."""

import io
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from PIL import Image, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import database_session
from app.modules.admin.sql_audit import SqlAdminAuditTrail
from app.modules.community.domain import CommunityReport, ReportAppeal, ReportCategory
from app.modules.community.media import (
    CommunityMediaLifecycle,
    MediaStorageError,
    MediaUnavailableError,
)
from app.modules.community.s3_media import S3CommunityMediaStore
from app.modules.community.schemas import (
    AppealCreate,
    AppealResolution,
    AppealResponse,
    MediaAccessResponse,
    MediaPurgeResponse,
    ModerationCommand,
    ReportCreate,
    ReportResponse,
)
from app.modules.community.service import (
    CommunityReportService,
    DuplicateReportError,
    InvalidReportError,
)
from app.modules.community.sql_repository import SqlCommunityReportRepository
from app.modules.identity.domain import User
from app.presentation.api.routes.admin import privileged_user
from app.presentation.api.routes.auth import current_user
from app.shared.config import get_settings

router = APIRouter()


@lru_cache(maxsize=4)
def _configured_media_store(bucket: str) -> S3CommunityMediaStore:
    return S3CommunityMediaStore(bucket)


def community_media_store() -> S3CommunityMediaStore | None:
    bucket = get_settings().media_bucket
    return _configured_media_store(bucket) if bucket else None


def media_lifecycle(
    repository: SqlCommunityReportRepository,
    store: S3CommunityMediaStore | None,
) -> CommunityMediaLifecycle | None:
    if store is None:
        return None
    return CommunityMediaLifecycle(
        repository, store, retention_days=get_settings().media_retention_days
    )


def community_repository(
    session: Annotated[AsyncSession, Depends(database_session)],
) -> SqlCommunityReportRepository:
    return SqlCommunityReportRepository(session)


def admin_audit_trail(
    session: Annotated[AsyncSession, Depends(database_session)],
) -> SqlAdminAuditTrail:
    return SqlAdminAuditTrail(session)


def response(report: CommunityReport) -> ReportResponse:
    return ReportResponse.model_validate(report, from_attributes=True)


def appeal_response(appeal: ReportAppeal) -> AppealResponse:
    return AppealResponse.model_validate(appeal, from_attributes=True)


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(
    command: ReportCreate,
    user: Annotated[User, Depends(current_user)],
    repository: Annotated[SqlCommunityReportRepository, Depends(community_repository)],
) -> ReportResponse:
    try:
        report = await CommunityReportService(repository).submit(
            user.id,
            command.category,
            command.latitude,
            command.longitude,
            command.description,
        )
    except DuplicateReportError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except InvalidReportError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return response(report)


@router.post("/with-photo", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report_with_photo(
    user: Annotated[User, Depends(current_user)],
    repository: Annotated[SqlCommunityReportRepository, Depends(community_repository)],
    store: Annotated[S3CommunityMediaStore | None, Depends(community_media_store)],
    category: Annotated[ReportCategory, Form()],
    latitude: Annotated[float, Form(ge=-90, le=90)],
    longitude: Annotated[float, Form(ge=-180, le=180)],
    description: Annotated[str, Form(min_length=12, max_length=1000)],
    photo: Annotated[UploadFile, File()],
) -> ReportResponse:
    if photo.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "unsupported image type")
    payload = await photo.read(10 * 1024 * 1024 + 1)
    if not payload or len(payload) > 10 * 1024 * 1024:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "image exceeds 10 MB")
    try:
        with Image.open(io.BytesIO(payload)) as image:
            image.verify()
            if image.width * image.height > 24_000_000:
                raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "image exceeds 24 MP")
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid image") from error
    try:
        report = await CommunityReportService(
            repository, media_lifecycle(repository, store)
        ).submit(
            user.id,
            category,
            latitude,
            longitude,
            description,
            payload,
            photo.content_type,
        )
    except DuplicateReportError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except InvalidReportError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    except MediaStorageError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "community media storage unavailable"
        ) from error
    return response(report)


@router.post("/media/purge", response_model=MediaPurgeResponse)
async def purge_report_media(
    actor: Annotated[User, Depends(privileged_user)],
    repository: Annotated[SqlCommunityReportRepository, Depends(community_repository)],
    audit: Annotated[SqlAdminAuditTrail, Depends(admin_audit_trail)],
    store: Annotated[S3CommunityMediaStore | None, Depends(community_media_store)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> MediaPurgeResponse:
    if store is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "community media storage is disabled"
        )
    result = await CommunityMediaLifecycle(
        repository, store, retention_days=get_settings().media_retention_days
    ).purge_expired(limit=limit)
    await audit.append(actor.id, "community.media_purged")
    return MediaPurgeResponse(scanned=result.scanned, deleted=result.deleted, failed=result.failed)


@router.get("/moderation", response_model=list[ReportResponse])
async def moderation_queue(
    _: Annotated[User, Depends(privileged_user)],
    repository: Annotated[SqlCommunityReportRepository, Depends(community_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ReportResponse]:
    return [response(report) for report in await repository.pending(limit)]


@router.get("/{report_id}/media-access", response_model=MediaAccessResponse)
async def access_report_media(
    report_id: UUID,
    actor: Annotated[User, Depends(privileged_user)],
    repository: Annotated[SqlCommunityReportRepository, Depends(community_repository)],
    audit: Annotated[SqlAdminAuditTrail, Depends(admin_audit_trail)],
    store: Annotated[S3CommunityMediaStore | None, Depends(community_media_store)],
    http_response: Response,
    expires_seconds: Annotated[int, Query(ge=30, le=300)] = 60,
) -> MediaAccessResponse:
    if store is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "community media storage is disabled"
        )
    try:
        grant = await CommunityMediaLifecycle(
            repository, store, retention_days=get_settings().media_retention_days
        ).create_access_grant(report_id, expires_seconds=expires_seconds)
    except MediaUnavailableError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except MediaStorageError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "community media access unavailable"
        ) from error
    await audit.append(actor.id, "community.media_accessed", report_id)
    http_response.headers["Cache-Control"] = "private, no-store"
    http_response.headers["Pragma"] = "no-cache"
    return MediaAccessResponse(url=grant.url, expires_at=grant.expires_at)


@router.post("/{report_id}/moderate", response_model=ReportResponse)
async def moderate_report(
    report_id: UUID,
    command: ModerationCommand,
    actor: Annotated[User, Depends(privileged_user)],
    repository: Annotated[SqlCommunityReportRepository, Depends(community_repository)],
    audit: Annotated[SqlAdminAuditTrail, Depends(admin_audit_trail)],
    store: Annotated[S3CommunityMediaStore | None, Depends(community_media_store)],
) -> ReportResponse:
    try:
        report = await CommunityReportService(
            repository, media_lifecycle(repository, store)
        ).moderate(report_id, command.approved, command.reason)
    except InvalidReportError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except MediaStorageError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "community media deletion unavailable"
        ) from error
    action = "community.report_approved" if command.approved else "community.report_rejected"
    await audit.append(actor.id, action, report.id)
    return response(report)


@router.post("/{report_id}/appeals", response_model=AppealResponse, status_code=201)
async def appeal_report(
    report_id: UUID,
    command: AppealCreate,
    user: Annotated[User, Depends(current_user)],
    repository: Annotated[SqlCommunityReportRepository, Depends(community_repository)],
) -> AppealResponse:
    try:
        appeal = await CommunityReportService(repository).appeal(
            report_id, user.id, command.reason
        )
    except DuplicateReportError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except InvalidReportError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return appeal_response(appeal)


@router.post("/appeals/{appeal_id}/resolve", response_model=AppealResponse)
async def resolve_appeal(
    appeal_id: UUID,
    command: AppealResolution,
    actor: Annotated[User, Depends(privileged_user)],
    repository: Annotated[SqlCommunityReportRepository, Depends(community_repository)],
    audit: Annotated[SqlAdminAuditTrail, Depends(admin_audit_trail)],
) -> AppealResponse:
    try:
        appeal = await CommunityReportService(repository).resolve_appeal(
            appeal_id, command.overturned, command.reason
        )
    except InvalidReportError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    action = "community.appeal_overturned" if command.overturned else "community.appeal_upheld"
    await audit.append(actor.id, action, appeal.report_id)
    return appeal_response(appeal)
