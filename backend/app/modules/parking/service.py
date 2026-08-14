"""Parking map and fail-closed parking-decision application use cases."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.modules.parking.domain import (
    CoverageStatus,
    ParkingDecisionOutcome,
    ParkingDecisionReasonCode,
    ParkingZone,
    ParkingZoneRepository,
    Provenance,
    TemporalRuleEffect,
    ZoneType,
)


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

    async def expired_decision(self, longitude: float, latitude: float) -> ParkingZone | None:
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise InvalidViewportError("invalid coordinates")
        return await self._zones.at_location(longitude, latitude, include_expired=True)


@dataclass(frozen=True, slots=True)
class ParkingDecisionReason:
    code: ParkingDecisionReasonCode
    message: str


@dataclass(frozen=True, slots=True)
class ParkingDecision:
    outcome: ParkingDecisionOutcome
    coverage_status: CoverageStatus
    reasons: tuple[ParkingDecisionReason, ...]
    zone: ParkingZone | None
    evaluated_at: datetime
    decision_rule_id: str | None = None


class ParkingDecisionService:
    """Authoritative decision evaluator; clients must only render this result."""

    maximum_accuracy_meters = 20.0
    maximum_location_age = timedelta(minutes=2)

    def __init__(self, parking: ParkingMapService) -> None:
        self._parking = parking

    async def evaluate(
        self,
        longitude: float,
        latitude: float,
        *,
        accuracy_meters: float,
        located_at: datetime,
        location_consent: bool,
        has_resident_permit: bool = False,
        now: datetime | None = None,
    ) -> ParkingDecision:
        evaluated_at = now or datetime.now(UTC)
        if not location_consent:
            return self._indeterminate(
                CoverageStatus.LOCATION_CONSENT_REQUIRED,
                ParkingDecisionReasonCode.LOCATION_CONSENT_REQUIRED,
                "Location consent is required to evaluate parking at this location.",
                evaluated_at,
            )
        if accuracy_meters > self.maximum_accuracy_meters:
            return self._indeterminate(
                CoverageStatus.LOCATION_PRECISION_INSUFFICIENT,
                ParkingDecisionReasonCode.LOCATION_PRECISION_INSUFFICIENT,
                "Location accuracy is not sufficient for a parking decision.",
                evaluated_at,
            )
        if located_at.tzinfo is None or abs(evaluated_at - located_at) > self.maximum_location_age:
            return self._indeterminate(
                CoverageStatus.LOCATION_STALE,
                ParkingDecisionReasonCode.DECISION_INDETERMINATE,
                "Location is too old to make a parking decision.",
                evaluated_at,
            )

        zone = await self._parking.decision(longitude, latitude)
        if zone is None:
            expired = await self._parking.expired_decision(longitude, latitude)
            if expired is not None:
                return self._indeterminate(
                    CoverageStatus.STALE_DATA,
                    ParkingDecisionReasonCode.STALE_DATA,
                    "Parking evidence for this location is no longer current.",
                    evaluated_at,
                    expired,
                )
            return self._indeterminate(
                CoverageStatus.NO_VERIFIED_COVERAGE,
                ParkingDecisionReasonCode.NO_VERIFIED_COVERAGE,
                "No verified parking evidence covers this location.",
                evaluated_at,
            )
        if zone.provenance is not Provenance.OFFICIAL or zone.confidence < 0.9:
            return self._indeterminate(
                CoverageStatus.UNVERIFIABLE_SOURCE,
                ParkingDecisionReasonCode.UNVERIFIABLE_SOURCE,
                "Parking evidence for this location is not verified for a decision.",
                evaluated_at,
                zone,
            )
        temporal = self._temporal_decision(zone, evaluated_at)
        if temporal is not None:
            return temporal
        return self._from_verified_zone(zone, has_resident_permit, evaluated_at)

    @staticmethod
    def _temporal_decision(zone: ParkingZone, evaluated_at: datetime) -> ParkingDecision | None:
        if not zone.temporal_schedule_required and not zone.temporal_rules:
            return None
        if not zone.temporal_rules:
            return ParkingDecisionService._indeterminate(
                CoverageStatus.VERIFIED_COVERAGE,
                ParkingDecisionReasonCode.TEMPORAL_RULE_INDETERMINATE,
                "Verified parking evidence requires a current temporal schedule.",
                evaluated_at,
                zone,
            )
        active = []
        for rule in zone.temporal_rules:
            try:
                local = evaluated_at.astimezone(ZoneInfo(rule.timezone))
            except ZoneInfoNotFoundError:
                return ParkingDecisionService._indeterminate(
                    CoverageStatus.VERIFIED_COVERAGE,
                    ParkingDecisionReasonCode.TEMPORAL_RULE_INDETERMINATE,
                    "Parking schedule timezone is not verifiable.",
                    evaluated_at,
                    zone,
                )
            invalid = (
                not rule.rule_id
                or not rule.weekdays
                or any(day not in range(7) for day in rule.weekdays)
                or rule.window.starts_at == rule.window.ends_at
                or rule.valid_from.tzinfo is None
                or rule.valid_until is None
                or rule.valid_until.tzinfo is None
                or rule.valid_until <= rule.valid_from
            )
            if invalid:
                return ParkingDecisionService._indeterminate(
                    CoverageStatus.VERIFIED_COVERAGE,
                    ParkingDecisionReasonCode.TEMPORAL_RULE_INDETERMINATE,
                    "Parking schedule is incomplete.",
                    evaluated_at,
                    zone,
                )
            if rule.valid_until is None:
                return ParkingDecisionService._indeterminate(
                    CoverageStatus.VERIFIED_COVERAGE,
                    ParkingDecisionReasonCode.TEMPORAL_RULE_INDETERMINATE,
                    "Parking schedule is incomplete.",
                    evaluated_at,
                    zone,
                )
            if evaluated_at >= rule.valid_until:
                continue
            if (
                evaluated_at < rule.valid_from
                or local.weekday() not in rule.weekdays
                or local.date() in rule.exception_dates
            ):
                continue
            local_time = local.timetz().replace(tzinfo=None)
            if not ParkingDecisionService._in_window(
                local_time, rule.window.starts_at, rule.window.ends_at
            ):
                continue
            if any(
                ParkingDecisionService._in_window(local_time, item.starts_at, item.ends_at)
                for item in rule.not_applicable_windows
            ):
                continue
            active.append(rule)
        if not active:
            return ParkingDecisionService._indeterminate(
                CoverageStatus.VERIFIED_COVERAGE,
                ParkingDecisionReasonCode.TEMPORAL_RULE_INDETERMINATE,
                "No current parking rule applies at this time.",
                evaluated_at,
                zone,
            )
        # Explicit conservative precedence makes overlapping rules deterministic.
        priority = {
            TemporalRuleEffect.PARK: 0,
            TemporalRuleEffect.CAUTION: 1,
            TemporalRuleEffect.DO_NOT_PARK: 2,
        }
        selected = max(active, key=lambda item: priority[item.effect])
        outcome = ParkingDecisionOutcome(selected.effect.value)
        return ParkingDecision(
            outcome,
            CoverageStatus.VERIFIED_COVERAGE,
            (
                ParkingDecisionReason(
                    ParkingDecisionReasonCode.OFFICIAL_RESTRICTION,
                    "Official current parking schedule applies.",
                ),
            ),
            zone,
            evaluated_at,
            selected.rule_id,
        )

    @staticmethod
    def _in_window(value, starts, ends) -> bool:
        return starts <= value < ends if starts < ends else value >= starts or value < ends

    @staticmethod
    def _indeterminate(
        coverage_status: CoverageStatus,
        code: ParkingDecisionReasonCode,
        message: str,
        evaluated_at: datetime,
        zone: ParkingZone | None = None,
    ) -> ParkingDecision:
        return ParkingDecision(
            ParkingDecisionOutcome.INDETERMINATE,
            coverage_status,
            (ParkingDecisionReason(code, message),),
            zone,
            evaluated_at,
        )

    @staticmethod
    def _from_verified_zone(
        zone: ParkingZone, has_resident_permit: bool, evaluated_at: datetime
    ) -> ParkingDecision:
        if zone.zone_type is ZoneType.PRIVATE_PROPERTY:
            return ParkingDecision(
                ParkingDecisionOutcome.DO_NOT_PARK,
                CoverageStatus.VERIFIED_COVERAGE,
                (
                    ParkingDecisionReason(
                        ParkingDecisionReasonCode.OFFICIAL_RESTRICTION,
                        "Official evidence identifies private property requiring owner permission.",
                    ),
                ),
                zone,
                evaluated_at,
            )
        if zone.zone_type is ZoneType.RESIDENT_ONLY and not has_resident_permit:
            return ParkingDecision(
                ParkingDecisionOutcome.DO_NOT_PARK,
                CoverageStatus.VERIFIED_COVERAGE,
                (
                    ParkingDecisionReason(
                        ParkingDecisionReasonCode.RESIDENT_PERMIT_REQUIRED,
                        "Official evidence requires a resident permit.",
                    ),
                ),
                zone,
                evaluated_at,
            )
        if zone.towing_hotspot or zone.zone_type is ZoneType.TOWING_HOTSPOT:
            return ParkingDecision(
                ParkingDecisionOutcome.DO_NOT_PARK,
                CoverageStatus.VERIFIED_COVERAGE,
                (
                    ParkingDecisionReason(
                        ParkingDecisionReasonCode.TOWING_RISK,
                        "Official evidence identifies elevated towing risk.",
                    ),
                ),
                zone,
                evaluated_at,
            )
        outcome = (
            ParkingDecisionOutcome.PARK
            if zone.parking_score >= 75
            else ParkingDecisionOutcome.CAUTION
        )
        return ParkingDecision(
            outcome,
            CoverageStatus.VERIFIED_COVERAGE,
            (
                ParkingDecisionReason(
                    ParkingDecisionReasonCode.OFFICIAL_RESTRICTION,
                    "Official parking evidence is current for this location.",
                ),
            ),
            zone,
            evaluated_at,
        )
