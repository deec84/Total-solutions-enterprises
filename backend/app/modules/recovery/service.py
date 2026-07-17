"""Towing recovery orchestration without retaining vehicle identifiers."""

import re

from app.modules.recovery.domain import RecoveryResult, TowLookupProvider


class InvalidVehicleIdentifier(ValueError):
    pass


class TowingRecoveryService:
    def __init__(self, provider: TowLookupProvider) -> None:
        self._provider = provider

    async def lookup(
        self, state: str, license_plate: str, vin_last_six: str | None = None
    ) -> RecoveryResult:
        normalized_state = state.strip().upper()
        normalized_plate = re.sub(r"[ -]", "", license_plate.strip().upper())
        normalized_vin = vin_last_six.strip().upper() if vin_last_six else None
        if not re.fullmatch(r"[A-Z]{2}", normalized_state):
            raise InvalidVehicleIdentifier("state must be a two-letter code")
        if not re.fullmatch(r"[A-Z0-9]{2,12}", normalized_plate):
            raise InvalidVehicleIdentifier("license plate format is invalid")
        if normalized_vin and not re.fullmatch(r"[A-HJ-NPR-Z0-9]{6}", normalized_vin):
            raise InvalidVehicleIdentifier("VIN suffix format is invalid")

        record = await self._provider.lookup(normalized_state, normalized_plate, normalized_vin)
        if record is None:
            return RecoveryResult(
                found=False,
                message=(
                    "No verified tow record was found. Recheck the vehicle details and contact "
                    "the local non-emergency authority before paying any third party."
                ),
            )
        return RecoveryResult(
            found=True,
            message="A verified towing record was found. Confirm fees directly before travel.",
            record=record,
        )
