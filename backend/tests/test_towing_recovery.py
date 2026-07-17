import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.modules.identity.domain import Role, User
from app.modules.parking.domain import Provenance
from app.modules.recovery.domain import TowRecord
from app.modules.recovery.providers import (
    DisabledTowLookupProvider,
    HttpTowLookupProvider,
    RecoveryProviderUnavailable,
)
from app.modules.recovery.service import InvalidVehicleIdentifier, TowingRecoveryService
from app.presentation.api.routes.auth import current_user
from app.presentation.api.routes.recovery import towing_recovery_service


class FakeProvider:
    def __init__(self, record: TowRecord | None) -> None:
        self.record = record
        self.received: tuple[str, str, str | None] | None = None

    async def lookup(
        self, state: str, license_plate: str, vin_last_six: str | None
    ) -> TowRecord | None:
        self.received = (state, license_plate, vin_last_six)
        return self.record


def tow_record() -> TowRecord:
    return TowRecord(
        tow_company="City Tow Services",
        storage_location="100 Secure Lot Drive, Miami, FL",
        phone_number="+1-305-555-0100",
        business_hours="Open 24 hours",
        required_documents=("Government photo ID", "Vehicle registration"),
        estimated_fees_cents=24500,
        payment_methods=("Credit card", "Cash"),
        navigation_url="https://maps.example.com/?q=secure+lot",
        provenance=Provenance.OFFICIAL,
        confidence=0.98,
        last_verified_at=datetime(2026, 7, 17, tzinfo=UTC),
    )


def test_recovery_normalizes_identifiers_and_returns_verified_record() -> None:
    async def scenario() -> None:
        provider = FakeProvider(tow_record())
        result = await TowingRecoveryService(provider).lookup(" fl ", " ab-12 3 ", "123abc")
        assert result.found and result.record == tow_record()
        assert provider.received == ("FL", "AB123", "123ABC")

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("state", "plate", "vin"),
    [("Florida", "ABC123", None), ("FL", "!", None), ("FL", "ABC123", "IIIIII")],
)
def test_recovery_rejects_invalid_vehicle_identifiers(
    state: str, plate: str, vin: str | None
) -> None:
    with pytest.raises(InvalidVehicleIdentifier):
        asyncio.run(TowingRecoveryService(FakeProvider(None)).lookup(state, plate, vin))


def test_disabled_provider_returns_safe_not_found_guidance() -> None:
    result = asyncio.run(
        TowingRecoveryService(DisabledTowLookupProvider()).lookup("FL", "ABC123")
    )
    assert not result.found
    assert "non-emergency" in result.message


def test_http_provider_maps_contracted_response_and_hides_failures() -> None:
    payload = {
        "found": True,
        "record": {
            "tow_company": "City Tow Services",
            "storage_location": "100 Secure Lot Drive, Miami, FL",
            "phone_number": "+1-305-555-0100",
            "business_hours": "Open 24 hours",
            "required_documents": ["Government photo ID"],
            "estimated_fees_cents": 24500,
            "payment_methods": ["Credit card"],
            "navigation_url": "https://maps.example.com/lot",
            "provenance": "official",
            "confidence": 0.98,
            "last_verified_at": "2026-07-17T12:00:00+00:00",
        },
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer provider-secret"
        return httpx.Response(200, json=payload)

    provider = HttpTowLookupProvider(
        "https://provider.example.com/lookup",
        "provider-secret",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    record = asyncio.run(provider.lookup("FL", "ABC123", None))
    assert record is not None and record.provenance is Provenance.OFFICIAL

    broken = HttpTowLookupProvider(
        "https://provider.example.com/lookup",
        "provider-secret",
        lambda: httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(500))
        ),
    )
    with pytest.raises(RecoveryProviderUnavailable):
        asyncio.run(broken.lookup("FL", "ABC123", None))


def test_recovery_http_contract_is_authenticated_and_never_cached() -> None:
    user = User(
        uuid4(), "driver@example.com", "hash", Role.USER, True, True, datetime.now(UTC)
    )
    application = create_app()
    application.dependency_overrides[current_user] = lambda: user
    application.dependency_overrides[towing_recovery_service] = lambda: TowingRecoveryService(
        FakeProvider(tow_record())
    )
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/recovery/lookup",
            json={"state": "FL", "license_plate": "ABC123"},
        )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.json()["record"]["tow_company"] == "City Tow Services"
    assert "not retained" in response.json()["privacy_notice"]
