"""PostGIS viewport adapter for parking zones."""

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import ParkingZoneRow
from app.modules.parking.domain import ParkingZone, Provenance, ZoneType


class SqlParkingZoneRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def in_viewport(
        self, west: float, south: float, east: float, north: float, limit: int
    ) -> tuple[ParkingZone, ...]:
        envelope = func.ST_MakeEnvelope(west, south, east, north, 4326)
        statement = (
            select(ParkingZoneRow, func.ST_AsGeoJSON(ParkingZoneRow.geometry))
            .where(
                func.ST_Intersects(ParkingZoneRow.geometry, envelope),
                (ParkingZoneRow.expires_at.is_(None))
                | (ParkingZoneRow.expires_at > func.now()),
            )
            .order_by(ParkingZoneRow.parking_score)
            .limit(limit)
        )
        rows = (await self._session.execute(statement)).all()
        return tuple(self._map(row, geojson) for row, geojson in rows)

    async def at_location(self, longitude: float, latitude: float) -> ParkingZone | None:
        point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        provenance_priority = case(
            (ParkingZoneRow.provenance == Provenance.OFFICIAL.value, 0),
            (ParkingZoneRow.provenance == Provenance.COMMUNITY_VERIFIED.value, 1),
            (ParkingZoneRow.provenance == Provenance.AI_PREDICTION.value, 2),
            else_=3,
        )
        statement = (
            select(ParkingZoneRow, func.ST_AsGeoJSON(ParkingZoneRow.geometry))
            .where(
                func.ST_Covers(ParkingZoneRow.geometry, point),
                (ParkingZoneRow.expires_at.is_(None))
                | (ParkingZoneRow.expires_at > func.now()),
            )
            .order_by(provenance_priority, ParkingZoneRow.parking_score)
            .limit(1)
        )
        result = (await self._session.execute(statement)).first()
        return self._map(result[0], result[1]) if result is not None else None

    @staticmethod
    def _map(row: ParkingZoneRow, geojson: str) -> ParkingZone:
        return ParkingZone(
            id=row.id,
            name=row.name,
            zone_type=ZoneType(row.zone_type),
            geometry_geojson=geojson,
            parking_score=row.parking_score,
            provenance=Provenance(row.provenance),
            confidence=row.confidence,
            restriction_summary=row.restriction_summary,
            average_towing_cost_cents=row.average_towing_cost_cents,
            towing_hotspot=row.towing_hotspot,
            observed_at=row.observed_at,
            expires_at=row.expires_at,
        )
