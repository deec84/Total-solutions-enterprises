"""Privacy-safe towing recovery contracts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.modules.parking.domain import Provenance


@dataclass(frozen=True, slots=True)
class TowRecord:
    tow_company: str
    storage_location: str
    phone_number: str
    business_hours: str
    required_documents: tuple[str, ...]
    estimated_fees_cents: int | None
    payment_methods: tuple[str, ...]
    navigation_url: str
    provenance: Provenance
    confidence: float
    last_verified_at: datetime


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    found: bool
    message: str
    record: TowRecord | None = None


class TowLookupProvider(Protocol):
    async def lookup(
        self, state: str, license_plate: str, vin_last_six: str | None
    ) -> TowRecord | None: ...
