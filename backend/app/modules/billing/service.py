"""Fail-closed purchase reconciliation and entitlement evaluation."""

import hashlib
import hmac
from datetime import UTC, datetime
from uuid import UUID, uuid4, uuid5

from app.modules.billing.domain import (
    BillingEvent,
    BillingProduct,
    BillingRepository,
    EntitlementSnapshot,
    PurchaseVerificationRequest,
    StoreEnvironment,
    StorePlatform,
    StorePurchaseVerifier,
    SubscriptionRecord,
    SubscriptionStatus,
    VerifiedPurchase,
)
from app.modules.observability.redaction import log_integration_failure


class BillingError(ValueError):
    """Safe purchase or product validation error."""


class BillingUnavailable(RuntimeError):
    """Purchase verification is disabled or its provider is unavailable."""


class BillingService:
    def __init__(
        self,
        repository: BillingRepository,
        verifier: StorePurchaseVerifier,
        subject_secret: str,
        products: tuple[BillingProduct, ...],
        enabled: bool,
        allowed_environments: frozenset[StoreEnvironment],
    ) -> None:
        if len(subject_secret) < 32:
            raise ValueError("billing subject secret must contain at least 32 characters")
        product_keys = {(item.platform, item.product_id) for item in products}
        if len(product_keys) != len(products) or any(
            not item.product_id.strip() or len(item.product_id) > 200
            for item in products
        ):
            raise ValueError("billing products must have unique bounded identifiers")
        if not allowed_environments:
            raise ValueError("at least one store environment must be allowed")
        self._repository = repository
        self._verifier = verifier
        self._subject_secret = subject_secret
        self._products = products
        self._enabled = enabled
        self._allowed_environments = allowed_environments

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._products)

    @property
    def products(self) -> tuple[BillingProduct, ...]:
        return self._products

    async def entitlement(self, user_id: UUID) -> EntitlementSnapshot:
        current = await self._repository.current(user_id)
        if current is None:
            return EntitlementSnapshot("free", "inactive")
        now = datetime.now(UTC)
        active_status = current.status in {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.GRACE_PERIOD,
        }
        expired_by_time = current.expires_at is not None and current.expires_at <= now
        active = active_status and not expired_by_time
        effective_status = (
            SubscriptionStatus.EXPIRED if expired_by_time else current.status
        )
        return EntitlementSnapshot(
            tier=current.entitlement.value if active else "free",
            status=effective_status.value,
            platform=current.platform,
            product_id=current.product_id,
            expires_at=current.expires_at,
            auto_renews=current.auto_renews,
            last_verified_at=current.verified_at,
        )

    async def verify_purchase(
        self,
        user_id: UUID,
        platform: StorePlatform,
        product_id: str,
        signed_payload: str,
    ) -> EntitlementSnapshot:
        if not self.enabled:
            raise BillingUnavailable("store purchase verification is not enabled")
        product = next(
            (
                item
                for item in self._products
                if item.platform is platform and item.product_id == product_id
            ),
            None,
        )
        if product is None:
            raise BillingError("product is not in the approved store catalog")
        if not signed_payload.strip() or len(signed_payload) > 131_072:
            raise BillingError("signed store payload must contain at most 131072 characters")
        try:
            verified = await self._verifier.verify(
                PurchaseVerificationRequest(user_id, platform, product_id, signed_payload)
            )
        except BillingUnavailable as error:
            log_integration_failure("billing_verifier", "verify_purchase", error)
            raise
        except Exception as error:
            log_integration_failure("billing_verifier", "verify_purchase", error)
            raise BillingUnavailable("store purchase verification is unavailable") from error
        self._validate_verified(verified, user_id, product)
        subscription = self._subscription(verified)
        event = BillingEvent(
            uuid4(),
            subscription.id,
            self._reference(
                f"event:{verified.platform.value}:{verified.environment.value}",
                verified.provider_event_id,
            ),
            verified.status,
            verified.verified_at,
            datetime.now(UTC),
        )
        await self._repository.reconcile(subscription, event)
        return await self.entitlement(user_id)

    def _subscription(self, verified: VerifiedPurchase) -> SubscriptionRecord:
        original_reference = self._reference(
            f"original:{verified.platform.value}", verified.original_transaction_id
        )
        return SubscriptionRecord(
            uuid5(
                verified.user_id,
                f"{verified.platform.value}:{verified.environment.value}:{original_reference}",
            ),
            verified.user_id,
            self._subject(verified.user_id),
            verified.platform,
            verified.product_id,
            verified.entitlement,
            verified.status,
            verified.environment,
            self._reference(
                f"transaction:{verified.platform.value}", verified.transaction_id
            ),
            original_reference,
            verified.purchased_at,
            verified.expires_at,
            verified.verified_at,
            verified.auto_renews,
        )

    def _validate_verified(
        self, verified: VerifiedPurchase, user_id: UUID, product: BillingProduct
    ) -> None:
        timestamps = (verified.purchased_at, verified.verified_at, verified.expires_at)
        if any(item is not None and item.tzinfo is None for item in timestamps):
            raise BillingError("verified store timestamps must include a timezone")
        if verified.user_id != user_id:
            raise BillingError("verified purchase belongs to another account")
        if verified.platform is not product.platform or verified.product_id != product.product_id:
            raise BillingError("verified purchase does not match the requested product")
        if verified.entitlement is not product.entitlement:
            raise BillingError("verified purchase grants an unexpected entitlement")
        if verified.environment not in self._allowed_environments:
            raise BillingError("verified purchase is from an unapproved store environment")
        if verified.expires_at is not None and verified.expires_at <= verified.purchased_at:
            raise BillingError("verified subscription expiry is invalid")
        if verified.verified_at < verified.purchased_at:
            raise BillingError("store verification predates the purchase")

    def _subject(self, user_id: UUID) -> str:
        return self._reference("subject", user_id.hex)

    def _reference(self, namespace: str, value: str) -> str:
        return hmac.new(
            self._subject_secret.encode(),
            f"{namespace}:{value}".encode(),
            hashlib.sha256,
        ).hexdigest()
