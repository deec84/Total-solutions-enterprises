"""Provider-neutral billing and entitlement HTTP contracts."""

from pydantic import BaseModel, Field

from app.modules.billing.domain import EntitlementCode, StorePlatform


class BillingProductResponse(BaseModel):
    platform: StorePlatform
    product_id: str
    entitlement: EntitlementCode


class BillingConfigurationResponse(BaseModel):
    enabled: bool
    products: list[BillingProductResponse]
    pricing_source: str = "app_store_or_google_play"


class PurchaseVerificationCommand(BaseModel):
    platform: StorePlatform
    product_id: str = Field(min_length=1, max_length=200)
    signed_payload: str = Field(min_length=1, max_length=131_072)


class EntitlementResponse(BaseModel):
    tier: str
    status: str
    platform: StorePlatform | None
    product_id: str | None
    expires_at: str | None
    auto_renews: bool
    last_verified_at: str | None
