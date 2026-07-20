"""Municipal towing lookup adapters."""

from collections.abc import Callable
from datetime import datetime
from typing import Any

import httpx

from app.modules.observability.redaction import log_integration_failure
from app.modules.parking.domain import Provenance
from app.modules.recovery.domain import TowRecord


class RecoveryProviderUnavailable(RuntimeError):
    pass


class DisabledTowLookupProvider:
    async def lookup(
        self, state: str, license_plate: str, vin_last_six: str | None
    ) -> TowRecord | None:
        return None


class HttpTowLookupProvider:
    """Authenticated adapter for a contracted municipal-data gateway."""

    def __init__(
        self,
        endpoint: str,
        bearer_token: str,
        client_factory: Callable[[], httpx.AsyncClient] | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._bearer_token = bearer_token
        self._client_factory = client_factory or (lambda: httpx.AsyncClient(timeout=10))

    async def lookup(
        self, state: str, license_plate: str, vin_last_six: str | None
    ) -> TowRecord | None:
        try:
            async with self._client_factory() as client:
                response = await client.post(
                    self._endpoint,
                    headers={"Authorization": f"Bearer {self._bearer_token}"},
                    json={
                        "state": state,
                        "license_plate": license_plate,
                        "vin_last_six": vin_last_six,
                    },
                )
                response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or payload.get("found") is not True:
                return None
            record = payload.get("record")
            if not isinstance(record, dict):
                raise ValueError("missing tow record")
            return self._record(record)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            log_integration_failure("tow_lookup", "lookup_vehicle", error)
            raise RecoveryProviderUnavailable("towing lookup provider unavailable") from error

    @staticmethod
    def _record(value: dict[str, Any]) -> TowRecord:
        navigation_url = _required_string(value, "navigation_url")
        if not navigation_url.startswith("https://"):
            raise ValueError("navigation URL must use HTTPS")
        confidence = float(value["confidence"])
        if not 0 <= confidence <= 1:
            raise ValueError("invalid confidence")
        estimated_fees = value.get("estimated_fees_cents")
        if estimated_fees is not None:
            estimated_fees = int(estimated_fees)
            if estimated_fees < 0:
                raise ValueError("invalid fee")
        return TowRecord(
            tow_company=_required_string(value, "tow_company"),
            storage_location=_required_string(value, "storage_location"),
            phone_number=_required_string(value, "phone_number"),
            business_hours=_required_string(value, "business_hours"),
            required_documents=_string_tuple(value, "required_documents"),
            estimated_fees_cents=estimated_fees,
            payment_methods=_string_tuple(value, "payment_methods"),
            navigation_url=navigation_url,
            provenance=Provenance(str(value["provenance"])),
            confidence=confidence,
            last_verified_at=datetime.fromisoformat(str(value["last_verified_at"])),
        )


def _required_string(value: dict[str, Any], key: str) -> str:
    item = value[key]
    if not isinstance(item, str) or not item.strip():
        raise ValueError(f"invalid {key}")
    return item.strip()


def _string_tuple(value: dict[str, Any], key: str) -> tuple[str, ...]:
    items = value[key]
    if not isinstance(items, list) or not items:
        raise ValueError(f"invalid {key}")
    result = tuple(str(item).strip() for item in items if str(item).strip())
    if not result:
        raise ValueError(f"invalid {key}")
    return result
