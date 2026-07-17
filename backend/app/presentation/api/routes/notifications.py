"""Consent, device registration, and automatic location evaluation API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import database_session
from app.modules.identity.domain import User
from app.modules.notifications.domain import NotificationPreferences, PushProvider
from app.modules.notifications.providers import DisabledPushProvider, HttpPushProvider
from app.modules.notifications.schemas import (
    AlertDecisionResponse,
    DeviceRegistration,
    DeviceResponse,
    LocationEvaluation,
    PreferenceResponse,
    PreferenceUpdate,
)
from app.modules.notifications.service import (
    InvalidNotificationPreference,
    NotificationService,
)
from app.modules.notifications.sql_repository import SqlNotificationRepository
from app.modules.parking.service import ParkingMapService
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.parking import parking_map_service
from app.shared.config import get_settings

router = APIRouter()


def push_provider() -> PushProvider:
    settings = get_settings()
    if settings.push_provider_url and settings.push_provider_token:
        return HttpPushProvider(settings.push_provider_url, settings.push_provider_token)
    return DisabledPushProvider()


def notification_service(
    session: Annotated[AsyncSession, Depends(database_session)],
    parking: Annotated[ParkingMapService, Depends(parking_map_service)],
    provider: Annotated[PushProvider, Depends(push_provider)],
) -> NotificationService:
    return NotificationService(SqlNotificationRepository(session), provider, parking)


def preference_response(preferences: NotificationPreferences) -> PreferenceResponse:
    return PreferenceResponse.model_validate(preferences, from_attributes=True)


@router.get("/preferences", response_model=PreferenceResponse)
async def get_preferences(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(database_session)],
) -> PreferenceResponse:
    return preference_response(await SqlNotificationRepository(session).preferences(user.id))


@router.put("/preferences", response_model=PreferenceResponse)
async def update_preferences(
    command: PreferenceUpdate,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[NotificationService, Depends(notification_service)],
) -> PreferenceResponse:
    try:
        preferences = await service.update_preferences(user.id, **command.model_dump())
    except InvalidNotificationPreference as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return preference_response(preferences)


@router.post("/devices", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    command: DeviceRegistration,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[NotificationService, Depends(notification_service)],
) -> DeviceResponse:
    try:
        device = await service.register_device(user.id, command.platform, command.token)
    except InvalidNotificationPreference as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return DeviceResponse(id=str(device.id), platform=device.platform, enabled=device.enabled)


@router.post("/evaluate-location", response_model=AlertDecisionResponse)
async def evaluate_location(
    command: LocationEvaluation,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[NotificationService, Depends(notification_service)],
) -> AlertDecisionResponse:
    decision = await service.evaluate_location(user.id, command.latitude, command.longitude)
    return AlertDecisionResponse.model_validate(decision, from_attributes=True)
