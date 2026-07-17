"""In-memory facility adapter for deterministic unit and contract tests."""

import math
from datetime import UTC, datetime

from app.modules.recommendations.domain import (
    ParkingCandidate,
    ParkingFacility,
    ParkingFacilityRepository,
)


class InMemoryParkingFacilityRepository(ParkingFacilityRepository):
    def __init__(self, facilities: tuple[ParkingFacility, ...] = ()) -> None:
        self._facilities = facilities

    async def nearby(
        self, longitude: float, latitude: float, radius_meters: int, limit: int
    ) -> tuple[ParkingCandidate, ...]:
        now = datetime.now(UTC)
        candidates = [
            ParkingCandidate(facility, _distance(latitude, longitude, facility))
            for facility in self._facilities
            if facility.expires_at is None or facility.expires_at > now
        ]
        return tuple(
            sorted(
                (item for item in candidates if item.walking_distance_meters <= radius_meters),
                key=lambda item: item.walking_distance_meters,
            )[:limit]
        )


def _distance(latitude: float, longitude: float, facility: ParkingFacility) -> float:
    earth_radius_meters = 6_371_000
    latitude_1 = math.radians(latitude)
    latitude_2 = math.radians(facility.latitude)
    latitude_delta = math.radians(facility.latitude - latitude)
    longitude_delta = math.radians(facility.longitude - longitude)
    haversine = math.sin(latitude_delta / 2) ** 2 + (
        math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(longitude_delta / 2) ** 2
    )
    return 2 * earth_radius_meters * math.asin(math.sqrt(haversine))
