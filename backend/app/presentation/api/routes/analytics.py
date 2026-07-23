"""Consent-gated product-event intake with no raw identifiers in event storage."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import database_session
from app.modules.identity.domain import User
from app.modules.observability.schemas import ProductEventCommand, ProductEventResponse
from app.modules.privacy.domain import ConsentPurpose
from app.modules.privacy.sql_repository import SqlPrivacyRepository
from app.presentation.api.routes.auth import current_user

router = APIRouter()


@router.post(
    "/events",
    response_model=ProductEventResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def record_product_event(
    command: ProductEventCommand,
    request: Request,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(database_session)],
) -> ProductEventResponse:
    decisions = await SqlPrivacyRepository(session).latest_consents(user.id)
    granted = any(
        decision.purpose is ConsentPurpose.PRODUCT_ANALYTICS and decision.granted
        for decision in decisions
    )
    accepted = request.app.state.observability.analytics.track(
        user.id,
        command.name,
        command.properties,
        consent_granted=granted,
    )
    return ProductEventResponse(accepted=accepted)
