"""Disabled and authenticated store-verification gateway adapters."""

from collections.abc import Callable
from datetime import datetime
from urllib.parse import urlparse
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from app.modules.billing.domain import (
    EntitlementCode,
    PurchaseVerificationRequest,
    StoreEnvironment,
    StorePlatform,
    SubscriptionStatus,
    VerifiedPurchase,
)
from app.modules.billing.service import BillingUnavailable


class VerifiedPurchasePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    platform: StorePlatform
    product_id: str
    entitlement: EntitlementCode
    status: SubscriptionStatus
    environment: StoreEnvironment
    provider_event_id: str
    transaction_id: str
    original_transaction_id: str
    purchased_at: str
    expires_at: str | None
    verified_at: str
    auto_renews: bool


class DisabledStorePurchaseVerifier:
    async def verify(self, request: PurchaseVerificationRequest) -> VerifiedPurchase:
        raise BillingUnavailable("store purchase verification is not configured")


class HttpStorePurchaseVerifier:
    """Send opaque store evidence only to one preconfigured verification gateway."""

    def __init__(
        self,
        endpoint: str,
        bearer_token: str,
        client_factory: Callable[[], httpx.AsyncClient] | None = None,
    ) -> None:
        parsed = urlparse(endpoint)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "billing gateway must be an absolute HTTPS URL without "
                "credentials, queries, or fragments"
            )
        if not bearer_token:
            raise ValueError("billing gateway token is required")
        self._endpoint = endpoint
        self._bearer_token = bearer_token
        self._client_factory = client_factory or (lambda: httpx.AsyncClient(timeout=10))

    async def verify(self, request: PurchaseVerificationRequest) -> VerifiedPurchase:
        try:
            async with self._client_factory() as client:
                response = await client.post(
                    self._endpoint,
                    headers={"Authorization": f"Bearer {self._bearer_token}"},
                    json={
                        "user_id": str(request.user_id),
                        "platform": request.platform.value,
                        "product_id": request.product_id,
                        "signed_payload": request.signed_payload,
                    },
                )
                response.raise_for_status()
            if len(response.content) > 262_144:
                raise ValueError("billing gateway response exceeds the accepted bound")
            payload = VerifiedPurchasePayload.model_validate(response.json())
            return VerifiedPurchase(
                user_id=_uuid(payload.user_id),
                platform=payload.platform,
                product_id=_bounded(payload.product_id, 200),
                entitlement=payload.entitlement,
                status=payload.status,
                environment=payload.environment,
                provider_event_id=_bounded(payload.provider_event_id, 500),
                transaction_id=_bounded(payload.transaction_id, 500),
                original_transaction_id=_bounded(payload.original_transaction_id, 500),
                purchased_at=_datetime(payload.purchased_at),
                expires_at=(
                    _datetime(payload.expires_at) if payload.expires_at is not None else None
                ),
                verified_at=_datetime(payload.verified_at),
                auto_renews=payload.auto_renews,
            )
        except (httpx.HTTPError, ValidationError, TypeError, ValueError) as error:
            raise BillingUnavailable("store purchase verification gateway failed") from error


def _uuid(value: str) -> UUID:
    return UUID(value)


def _datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp timezone is required")
    return parsed


def _bounded(value: str, maximum: int) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        raise ValueError("provider string is outside the accepted bounds")
    return normalized
