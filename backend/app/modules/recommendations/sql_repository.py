"""PostGIS nearest-facility repository."""

from geoalchemy2 import Geography, Geometry
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import ParkingFacilityRow
from app.modules.parking.domain import Provenance
from app.modules.recommendations.domain import ParkingCandidate, ParkingFacility


class SqlParkingFacilityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def nearby(
        self, longitude: float, latitude: float, radius_meters: int, limit: int
    ) -> tuple[ParkingCandidate, ...]:
        point = cast(
            func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326),
            Geography("POINT", srid=4326),
        )
        distance = func.ST_Distance(ParkingFacilityRow.location, point)
        geometry = cast(ParkingFacilityRow.location, Geometry("POINT", srid=4326))
        statement = (
            select(
                ParkingFacilityRow,
                distance,
                func.ST_Y(geometry),
                func.ST_X(geometry),
            )
            .where(
                func.ST_DWithin(ParkingFacilityRow.location, point, radius_meters),
                (ParkingFacilityRow.expires_at.is_(None))
                | (ParkingFacilityRow.expires_at > func.now()),
            )
            .order_by(distance)
            .limit(limit)
        )
        rows = (await self._session.execute(statement)).all()
        return tuple(
            self._map(row, distance_meters, latitude_, longitude_)
            for row, distance_meters, latitude_, longitude_ in rows
        )

    @staticmethod
    def _map(
        row: ParkingFacilityRow,
        distance_meters: float,
        latitude: float,
        longitude: float,
    ) -> ParkingCandidate:
        return ParkingCandidate(
            facility=ParkingFacility(
                id=row.id,
                name=row.name,
                address=row.address,
                latitude=latitude,
                longitude=longitude,
                hourly_price_cents=row.hourly_price_cents,
                safety_score=row.safety_score,
                towing_incidents_per_1000=row.towing_incidents_per_1000,
                rating=row.rating,
                available_spaces=row.available_spaces,
                capacity=row.capacity,
                navigation_url=row.navigation_url,
                provenance=Provenance(row.provenance),
                confidence=row.confidence,
                observed_at=row.observed_at,
                expires_at=row.expires_at,
            ),
            walking_distance_meters=distance_meters,
        )
