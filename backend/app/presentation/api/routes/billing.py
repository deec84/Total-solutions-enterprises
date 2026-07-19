"""Authenticated, no-store subscription configuration and verification API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import database_session
from app.modules.billing.domain import (
    BillingProduct,
    EntitlementCode,
    EntitlementSnapshot,
    StoreEnvironment,
    StorePlatform,
    StorePurchaseVerifier,
)
from app.modules.billing.providers import (
    DisabledStorePurchaseVerifier,
    HttpStorePurchaseVerifier,
)
from app.modules.billing.schemas import (
    BillingConfigurationResponse,
    BillingProductResponse,
    EntitlementResponse,
    PurchaseVerificationCommand,
)
from app.modules.billing.service import BillingError, BillingService, BillingUnavailable
from app.modules.billing.sql_repository import SqlBillingRepository
from app.modules.identity.domain import User
from app.presentation.api.routes.auth import current_user
from app.shared.config import get_settings

router = APIRouter()


def _products() -> tuple[BillingProduct, ...]:
    settings = get_settings()
    values: list[BillingProduct] = []
    if settings.apple_premium_product_id:
        values.append(
            BillingProduct(
                StorePlatform.APPLE_APP_STORE,
                settings.apple_premium_product_id,
                EntitlementCode.PREMIUM,
            )
        )
    if settings.google_premium_product_id:
        values.append(
            BillingProduct(
                StorePlatform.GOOGLE_PLAY,
                settings.google_premium_product_id,
                EntitlementCode.PREMIUM,
            )
        )
    return tuple(values)


def billing_service(
    session: Annotated[AsyncSession, Depends(database_session)],
) -> BillingService:
    settings = get_settings()
    if (
        settings.billing_enabled
        and settings.billing_gateway_url
        and settings.billing_gateway_token
    ):
        verifier: StorePurchaseVerifier = HttpStorePurchaseVerifier(
            settings.billing_gateway_url, settings.billing_gateway_token
        )
    else:
        verifier = DisabledStorePurchaseVerifier()
    return BillingService(
        SqlBillingRepository(session),
        verifier,
        settings.billing_subject_secret,
        _products(),
        settings.billing_enabled,
        frozenset(
            {
                StoreEnvironment.PRODUCTION
                if settings.environment == "production"
                else StoreEnvironment.SANDBOX
            }
        ),
    )


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Pragma"] = "no-cache"


def entitlement_response(value: EntitlementSnapshot) -> EntitlementResponse:
    return EntitlementResponse(
        tier=value.tier,
        status=value.status,
        platform=value.platform,
        product_id=value.product_id,
        expires_at=value.expires_at.isoformat() if value.expires_at else None,
        auto_renews=value.auto_renews,
        last_verified_at=(
            value.last_verified_at.isoformat() if value.last_verified_at else None
        ),
    )


@router.get("/configuration", response_model=BillingConfigurationResponse)
async def configuration(
    response: Response,
    _: Annotated[User, Depends(current_user)],
    service: Annotated[BillingService, Depends(billing_service)],
) -> BillingConfigurationResponse:
    _no_store(response)
    return BillingConfigurationResponse(
        enabled=service.enabled,
        products=[
            BillingProductResponse(
                platform=item.platform,
                product_id=item.product_id,
                entitlement=item.entitlement,
            )
            for item in service.products
        ],
    )


@router.get("/entitlement", response_model=EntitlementResponse)
async def entitlement(
    response: Response,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[BillingService, Depends(billing_service)],
) -> EntitlementResponse:
    _no_store(response)
    return entitlement_response(await service.entitlement(user.id))


@router.post("/purchases/verify", response_model=EntitlementResponse)
async def verify_purchase(
    command: PurchaseVerificationCommand,
    response: Response,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[BillingService, Depends(billing_service)],
) -> EntitlementResponse:
    _no_store(response)
    try:
        value = await service.verify_purchase(
            user.id, command.platform, command.product_id, command.signed_payload
        )
    except BillingError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    except BillingUnavailable as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    return entitlement_response(value)
