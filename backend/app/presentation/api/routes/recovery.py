"""Authenticated, no-store towing recovery API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.modules.identity.domain import User
from app.modules.recovery.domain import RecoveryResult
from app.modules.recovery.providers import (
    DisabledTowLookupProvider,
    HttpTowLookupProvider,
    RecoveryProviderUnavailable,
)
from app.modules.recovery.schemas import TowLookupRequest, TowLookupResponse, TowRecordResponse
from app.modules.recovery.service import InvalidVehicleIdentifier, TowingRecoveryService
from app.presentation.api.routes.auth import current_user
from app.shared.config import get_settings

router = APIRouter()


def towing_recovery_service() -> TowingRecoveryService:
    settings = get_settings()
    if settings.tow_provider_url and settings.tow_provider_token:
        return TowingRecoveryService(
            HttpTowLookupProvider(settings.tow_provider_url, settings.tow_provider_token)
        )
    return TowingRecoveryService(DisabledTowLookupProvider())


@router.post("/lookup", response_model=TowLookupResponse)
async def lookup_towed_vehicle(
    command: TowLookupRequest,
    _: Annotated[User, Depends(current_user)],
    service: Annotated[TowingRecoveryService, Depends(towing_recovery_service)],
    response: Response,
) -> TowLookupResponse:
    response.headers["Cache-Control"] = "private, no-store"
    try:
        result = await service.lookup(
            command.state, command.license_plate, command.vin_last_six
        )
    except InvalidVehicleIdentifier as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    except RecoveryProviderUnavailable as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "towing lookup is temporarily unavailable",
        ) from error
    return _response(result)


def _response(result: RecoveryResult) -> TowLookupResponse:
    record = result.record
    return TowLookupResponse(
        found=result.found,
        message=result.message,
        record=(
            TowRecordResponse(
                tow_company=record.tow_company,
                storage_location=record.storage_location,
                phone_number=record.phone_number,
                business_hours=record.business_hours,
                required_documents=list(record.required_documents),
                estimated_fees_cents=record.estimated_fees_cents,
                payment_methods=list(record.payment_methods),
                navigation_url=record.navigation_url,
                provenance=record.provenance,
                confidence=record.confidence,
                last_verified_at=record.last_verified_at,
            )
            if record is not None
            else None
        ),
        privacy_notice="Vehicle identifiers are forwarded for this lookup and are not retained.",
    )
