"""Provider-neutral billing tests; every purchase artifact is synthetic."""

import asyncio
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.billing.domain import (
    BillingProduct,
    EntitlementCode,
    PurchaseVerificationRequest,
    StoreEnvironment,
    StorePlatform,
    SubscriptionStatus,
    VerifiedPurchase,
)
from app.modules.billing.providers import (
    DisabledStorePurchaseVerifier,
    HttpStorePurchaseVerifier,
)
from app.modules.billing.repositories import InMemoryBillingRepository
from app.modules.billing.service import BillingError, BillingService, BillingUnavailable
from app.modules.identity.domain import Role, User
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.billing import billing_service

PRODUCT_ID = "ai.parkshield.synthetic.premium"


def product() -> BillingProduct:
    return BillingProduct(
        StorePlatform.APPLE_APP_STORE, PRODUCT_ID, EntitlementCode.PREMIUM
    )


class SyntheticVerifier:
    def __init__(self, result: VerifiedPurchase | Exception) -> None:
        self.result = result
        self.requests: list[PurchaseVerificationRequest] = []

    async def verify(self, request: PurchaseVerificationRequest) -> VerifiedPurchase:
        self.requests.append(request)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def verified_purchase(
    user_id: UUID,
    *,
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
    verified_at: datetime | None = None,
    expires_at: datetime | None = None,
    **changes: object,
) -> VerifiedPurchase:
    purchased_at = datetime(2026, 7, 17, 12, tzinfo=UTC)
    base = VerifiedPurchase(
        user_id=user_id,
        platform=StorePlatform.APPLE_APP_STORE,
        product_id=PRODUCT_ID,
        entitlement=EntitlementCode.PREMIUM,
        status=status,
        environment=StoreEnvironment.SANDBOX,
        provider_event_id="synthetic-event-1",
        transaction_id="synthetic-transaction-1",
        original_transaction_id="synthetic-original-1",
        purchased_at=purchased_at,
        expires_at=expires_at or datetime.now(UTC) + timedelta(days=30),
        verified_at=verified_at or datetime.now(UTC),
        auto_renews=True,
    )
    return replace(base, **cast(dict[str, Any], changes))


def service(
    repository: InMemoryBillingRepository,
    verifier: SyntheticVerifier | DisabledStorePurchaseVerifier,
    *,
    enabled: bool = True,
) -> BillingService:
    return BillingService(
        repository,
        verifier,
        "synthetic-billing-subject-secret-at-least-32-characters",
        (product(),),
        enabled,
        frozenset({StoreEnvironment.SANDBOX}),
    )


def test_billing_service_is_free_until_verified_and_reconciles_idempotently() -> None:
    async def scenario() -> None:
        user_id = uuid4()
        repository = InMemoryBillingRepository()
        verifier = SyntheticVerifier(verified_purchase(user_id))
        billing = service(repository, verifier)

        free = await billing.entitlement(user_id)
        first = await billing.verify_purchase(
            user_id,
            StorePlatform.APPLE_APP_STORE,
            PRODUCT_ID,
            "SYNTHETIC SIGNED PAYLOAD — NOT A REAL STORE RECEIPT",
        )
        replay = await billing.verify_purchase(
            user_id,
            StorePlatform.APPLE_APP_STORE,
            PRODUCT_ID,
            "SYNTHETIC SIGNED PAYLOAD — NOT A REAL STORE RECEIPT",
        )
        persisted = await repository.current(user_id)

        assert free.tier == "free"
        assert first.tier == replay.tier == "premium"
        assert first.status == "active"
        assert len(repository.events()) == 1
        assert persisted is not None
        serialized = str(persisted)
        assert "SYNTHETIC SIGNED PAYLOAD" not in serialized
        assert "synthetic-transaction-1" not in serialized
        assert len(persisted.transaction_reference) == 64
        assert len(persisted.subject_reference) == 64

    asyncio.run(scenario())


def test_billing_service_rejects_unsafe_local_configuration() -> None:
    repository = InMemoryBillingRepository()
    verifier = DisabledStorePurchaseVerifier()
    with pytest.raises(ValueError, match="subject secret"):
        BillingService(
            repository,
            verifier,
            "short",
            (),
            False,
            frozenset({StoreEnvironment.SANDBOX}),
        )
    with pytest.raises(ValueError, match="unique bounded"):
        BillingService(
            repository,
            verifier,
            "synthetic-billing-subject-secret-at-least-32-characters",
            (product(), product()),
            False,
            frozenset({StoreEnvironment.SANDBOX}),
        )
    with pytest.raises(ValueError, match="store environment"):
        BillingService(
            repository,
            verifier,
            "synthetic-billing-subject-secret-at-least-32-characters",
            (),
            False,
            frozenset(),
        )


def test_billing_service_rejects_disabled_unapproved_and_untrusted_outcomes() -> None:
    async def scenario() -> None:
        user_id = uuid4()
        repository = InMemoryBillingRepository()
        disabled = service(repository, DisabledStorePurchaseVerifier(), enabled=False)
        with pytest.raises(BillingUnavailable, match="not enabled"):
            await disabled.verify_purchase(
                user_id, StorePlatform.APPLE_APP_STORE, PRODUCT_ID, "synthetic"
            )

        billing = service(repository, SyntheticVerifier(verified_purchase(user_id)))
        with pytest.raises(BillingError, match="catalog"):
            await billing.verify_purchase(
                user_id, StorePlatform.APPLE_APP_STORE, "unknown", "synthetic"
            )
        with pytest.raises(BillingError, match="signed store payload"):
            await billing.verify_purchase(
                user_id, StorePlatform.APPLE_APP_STORE, PRODUCT_ID, " "
            )

        invalid = [
            verified_purchase(uuid4()),
            verified_purchase(user_id, product_id="wrong"),
            verified_purchase(user_id, entitlement="unexpected"),
            verified_purchase(
                user_id,
                expires_at=datetime(2026, 7, 16, 12, tzinfo=UTC),
            ),
            verified_purchase(
                user_id,
                verified_at=datetime(2026, 7, 16, 12, tzinfo=UTC),
            ),
            verified_purchase(
                user_id,
                verified_at=datetime(2026, 7, 17, 13),
            ),
            verified_purchase(user_id, environment=StoreEnvironment.PRODUCTION),
        ]
        for evidence in invalid:
            untrusted = service(repository, SyntheticVerifier(evidence))
            with pytest.raises(BillingError):
                await untrusted.verify_purchase(
                    user_id, StorePlatform.APPLE_APP_STORE, PRODUCT_ID, "synthetic"
                )

        unavailable = service(repository, SyntheticVerifier(RuntimeError("provider detail")))
        with pytest.raises(BillingUnavailable, match="unavailable"):
            await unavailable.verify_purchase(
                user_id, StorePlatform.APPLE_APP_STORE, PRODUCT_ID, "synthetic"
            )

    asyncio.run(scenario())


def test_billing_entitlement_expires_conservatively_and_ignores_stale_updates() -> None:
    async def scenario() -> None:
        user_id = uuid4()
        repository = InMemoryBillingRepository()
        now = datetime.now(UTC)
        newer = verified_purchase(
            user_id,
            verified_at=now,
            status=SubscriptionStatus.REVOKED,
            provider_event_id="synthetic-newer-event",
        )
        older = verified_purchase(
            user_id,
            verified_at=now - timedelta(hours=1),
            status=SubscriptionStatus.ACTIVE,
            provider_event_id="synthetic-older-event",
        )
        billing = service(repository, SyntheticVerifier(newer))
        await billing.verify_purchase(
            user_id, StorePlatform.APPLE_APP_STORE, PRODUCT_ID, "synthetic-newer"
        )
        billing = service(repository, SyntheticVerifier(older))
        result = await billing.verify_purchase(
            user_id, StorePlatform.APPLE_APP_STORE, PRODUCT_ID, "synthetic-older"
        )

        assert result.tier == "free"
        assert result.status == "revoked"
        persisted = await repository.current(user_id)
        assert persisted is not None
        assert persisted.status is SubscriptionStatus.REVOKED

    asyncio.run(scenario())


def test_http_store_verifier_enforces_gateway_contract_without_real_provider_calls() -> None:
    async def scenario() -> None:
        user_id = uuid4()
        captured: dict[str, object] = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            captured["authorization"] = request.headers.get("Authorization")
            captured["body"] = request.content.decode()
            now = datetime.now(UTC)
            return httpx.Response(
                200,
                json={
                    "user_id": str(user_id),
                    "platform": "apple_app_store",
                    "product_id": PRODUCT_ID,
                    "entitlement": "premium",
                    "status": "active",
                    "environment": "sandbox",
                    "provider_event_id": "synthetic-event",
                    "transaction_id": "synthetic-transaction",
                    "original_transaction_id": "synthetic-original",
                    "purchased_at": (now - timedelta(minutes=1)).isoformat(),
                    "expires_at": (now + timedelta(days=30)).isoformat(),
                    "verified_at": now.isoformat(),
                    "auto_renews": True,
                },
            )

        transport = httpx.MockTransport(handler)
        verifier = HttpStorePurchaseVerifier(
            "https://billing-gateway.example.test/v1/verify",
            "synthetic-gateway-token",
            lambda: httpx.AsyncClient(transport=transport),
        )
        evidence = await verifier.verify(
            PurchaseVerificationRequest(
                user_id,
                StorePlatform.APPLE_APP_STORE,
                PRODUCT_ID,
                "synthetic-signed-payload",
            )
        )

        assert evidence.user_id == user_id
        assert evidence.environment is StoreEnvironment.SANDBOX
        assert captured["authorization"] == "Bearer synthetic-gateway-token"
        assert "synthetic-signed-payload" in str(captured["body"])

        with pytest.raises(ValueError):
            HttpStorePurchaseVerifier(
                "http://billing-gateway.example.test/v1/verify", "token"
            )
        with pytest.raises(ValueError):
            HttpStorePurchaseVerifier(
                "https://billing-gateway.example.test/v1/verify?token=unsafe", "token"
            )

    asyncio.run(scenario())


def test_http_store_verifier_rejects_provider_failure_and_malformed_success() -> None:
    async def scenario() -> None:
        user_id = uuid4()
        for response in (
            httpx.Response(503, json={"detail": "synthetic outage"}),
            httpx.Response(200, json={"verified": True}),
            httpx.Response(200, content=b"x" * 262_145),
        ):
            verifier = HttpStorePurchaseVerifier(
                "https://billing-gateway.example.test/v1/verify",
                "synthetic-token",
                lambda response=response: httpx.AsyncClient(
                    transport=httpx.MockTransport(lambda _: response)
                ),
            )
            with pytest.raises(BillingUnavailable, match="gateway failed"):
                await verifier.verify(
                    PurchaseVerificationRequest(
                        user_id,
                        StorePlatform.APPLE_APP_STORE,
                        PRODUCT_ID,
                        "synthetic",
                    )
                )

    asyncio.run(scenario())


@pytest.fixture
def billing_api() -> Iterator[TestClient]:
    user_id = uuid4()
    actor = User(
        user_id,
        "billing-test@example.com",
        "hash",
        Role.USER,
        True,
        True,
        datetime.now(UTC),
    )
    repository = InMemoryBillingRepository()
    verifier = SyntheticVerifier(verified_purchase(user_id))
    application = create_app()
    application.dependency_overrides[current_user] = lambda: actor
    application.dependency_overrides[billing_service] = lambda: service(
        repository, verifier
    )
    with TestClient(application) as client:
        yield client
    application.dependency_overrides.clear()


def test_billing_api_exposes_no_price_and_requires_real_verification_result(
    billing_api: TestClient,
) -> None:
    configuration = billing_api.get("/api/v1/billing/configuration")
    free = billing_api.get("/api/v1/billing/entitlement")
    verified = billing_api.post(
        "/api/v1/billing/purchases/verify",
        json={
            "platform": "apple_app_store",
            "product_id": PRODUCT_ID,
            "signed_payload": "SYNTHETIC SIGNED PAYLOAD — NOT A REAL RECEIPT",
        },
    )

    assert configuration.status_code == 200
    assert configuration.json()["enabled"] is True
    assert configuration.json()["pricing_source"] == "app_store_or_google_play"
    assert "price" not in str(configuration.json()).lower()
    assert free.json()["tier"] == "free"
    assert verified.json()["tier"] == "premium"
    assert verified.headers["cache-control"] == "private, no-store"


def test_billing_api_returns_fail_closed_disabled_state(billing_api: TestClient) -> None:
    disabled = BillingService(
        InMemoryBillingRepository(),
        DisabledStorePurchaseVerifier(),
        "synthetic-billing-subject-secret-at-least-32-characters",
        (product(),),
        False,
        frozenset({StoreEnvironment.SANDBOX}),
    )
    billing_api.app.dependency_overrides[billing_service] = lambda: disabled
    response = billing_api.post(
        "/api/v1/billing/purchases/verify",
        json={
            "platform": "apple_app_store",
            "product_id": PRODUCT_ID,
            "signed_payload": "synthetic",
        },
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "store purchase verification is not enabled"


def test_billing_dependency_remains_disabled_without_provider_configuration() -> None:
    dependency = billing_service(AsyncMock())
    assert dependency.enabled is False
