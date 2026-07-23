"""Authenticated privacy, consent, export, and account-deletion endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import database_session
from app.modules.identity.domain import User
from app.modules.identity.security import PasswordManager
from app.modules.privacy.domain import ConsentDecision, ConsentPurpose
from app.modules.privacy.schemas import (
    AccountDeletionCommand,
    ConsentCommand,
    ConsentResponse,
    DataExportResponse,
)
from app.modules.privacy.service import (
    ExternalDataDeletionError,
    PrivacyRequestError,
    PrivacyService,
)
from app.modules.privacy.sql_repository import SqlPrivacyRepository
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.community import community_media_store
from app.shared.config import get_settings

router = APIRouter()


def privacy_service(
    session: Annotated[AsyncSession, Depends(database_session)],
    request: Request,
) -> PrivacyService:
    settings = get_settings()
    return PrivacyService(
        SqlPrivacyRepository(session),
        PasswordManager(),
        settings.jwt_secret,
        settings.privacy_policy_version,
        community_media_store(),
        request.app.state.observability.analytics,
    )


def consent_response(decision: ConsentDecision) -> ConsentResponse:
    return ConsentResponse(
        purpose=decision.purpose,
        policy_version=decision.policy_version,
        granted=decision.granted,
        occurred_at=decision.occurred_at.isoformat(),
    )


@router.get("/consents", response_model=list[ConsentResponse])
async def consents(
    user: Annotated[User, Depends(current_user)],
    service: Annotated[PrivacyService, Depends(privacy_service)],
) -> list[ConsentResponse]:
    return [consent_response(item) for item in await service.consents(user.id)]


@router.put("/consents/{purpose}", response_model=ConsentResponse)
async def decide_consent(
    purpose: ConsentPurpose,
    command: ConsentCommand,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[PrivacyService, Depends(privacy_service)],
) -> ConsentResponse:
    return consent_response(
        await service.decide_consent(user.id, purpose, command.granted)
    )


@router.post("/export", response_model=DataExportResponse)
async def export_account_data(
    response: Response,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[PrivacyService, Depends(privacy_service)],
) -> DataExportResponse:
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Pragma"] = "no-cache"
    export = await service.export(user.id)
    return DataExportResponse(
        request_id=str(export.request_id),
        generated_at=export.generated_at.isoformat(),
        policy_version=export.policy_version,
        data=export.data,
    )


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    command: AccountDeletionCommand,
    request: Request,
    response: Response,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[PrivacyService, Depends(privacy_service)],
) -> None:
    try:
        await service.delete_account(
            user,
            command.password,
            command.confirmation,
            command.mfa_code,
        )
    except PrivacyRequestError as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
    except ExternalDataDeletionError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    response.headers["Cache-Control"] = "no-store"
    response.headers["Clear-Site-Data"] = '"cache", "storage"'
