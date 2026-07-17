"""Parking map application use cases."""

from app.modules.parking.domain import ParkingZone, ParkingZoneRepository


class InvalidViewportError(ValueError):
    pass


class ParkingMapService:
    def __init__(self, zones: ParkingZoneRepository) -> None:
        self._zones = zones

    async def viewport(
        self, west: float, south: float, east: float, north: float, limit: int = 500
    ) -> tuple[ParkingZone, ...]:
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise InvalidViewportError("invalid viewport bounds")
        bounded_limit = min(max(limit, 1), 1000)
        return await self._zones.in_viewport(west, south, east, north, bounded_limit)

    async def decision(self, longitude: float, latitude: float) -> ParkingZone | None:
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise InvalidViewportError("invalid coordinates")
        return await self._zones.at_location(longitude, latitude)
