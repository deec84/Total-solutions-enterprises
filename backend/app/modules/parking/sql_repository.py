"""PostGIS viewport adapter for parking zones."""

from datetime import date, datetime, time
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import ParkingZoneRow
from app.modules.parking.domain import (
    ParkingTemporalRule,
    ParkingZone,
    Provenance,
    TemporalRuleEffect,
    TemporalWindow,
    ZoneType,
)


def _rule(item: dict[str, Any]) -> ParkingTemporalRule:
    window = item["window"]
    if not isinstance(window, dict):
        raise ValueError("stored temporal window must be an object")
    return ParkingTemporalRule(
        str(item["rule_id"]),
        TemporalRuleEffect(str(item["effect"])),
        tuple(int(day) for day in item["weekdays"]),
        TemporalWindow(
            time.fromisoformat(str(window["starts_at"])), time.fromisoformat(str(window["ends_at"]))
        ),
        str(item["timezone"]),
        datetime.fromisoformat(str(item["valid_from"]).replace("Z", "+00:00")),
        datetime.fromisoformat(str(item["valid_until"]).replace("Z", "+00:00"))
        if item.get("valid_until")
        else None,
        tuple(date.fromisoformat(str(day)) for day in item.get("exception_dates", [])),
        tuple(
            TemporalWindow(
                time.fromisoformat(str(value["starts_at"])),
                time.fromisoformat(str(value["ends_at"])),
            )
            for value in item.get("not_applicable_windows", [])
        ),
        tuple(str(value) for value in item.get("special_restrictions", [])),
    )


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
                (ParkingZoneRow.expires_at.is_(None)) | (ParkingZoneRow.expires_at > func.now()),
            )
            .order_by(ParkingZoneRow.parking_score)
            .limit(limit)
        )
        rows = (await self._session.execute(statement)).all()
        return tuple(self._map(row, geojson) for row, geojson in rows)

    async def at_location(
        self, longitude: float, latitude: float, *, include_expired: bool = False
    ) -> ParkingZone | None:
        point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        provenance_priority = case(
            (ParkingZoneRow.provenance == Provenance.OFFICIAL.value, 0),
            (ParkingZoneRow.provenance == Provenance.COMMUNITY_VERIFIED.value, 1),
            (ParkingZoneRow.provenance == Provenance.AI_PREDICTION.value, 2),
            else_=3,
        )
        statement = (
            select(ParkingZoneRow, func.ST_AsGeoJSON(ParkingZoneRow.geometry))
            .where(func.ST_Covers(ParkingZoneRow.geometry, point))
            .order_by(provenance_priority, ParkingZoneRow.parking_score)
            .limit(1)
        )
        if not include_expired:
            statement = statement.where(
                (ParkingZoneRow.expires_at.is_(None)) | (ParkingZoneRow.expires_at > func.now())
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
            source_id=row.source_id,
            import_batch_id=row.import_batch_id,
            jurisdiction=row.jurisdiction,
            temporal_rules=tuple(_rule(item) for item in row.temporal_rules),
            temporal_schedule_required=row.temporal_schedule_required,
        )
