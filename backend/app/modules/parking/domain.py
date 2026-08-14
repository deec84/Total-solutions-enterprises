"""Parking risk domain and trust semantics."""

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class Provenance(StrEnum):
    OFFICIAL = "official"
    COMMUNITY_VERIFIED = "community_verified"
    AI_PREDICTION = "ai_prediction"
    ESTIMATED = "estimated"


class RiskLevel(StrEnum):
    VERY_SAFE = "very_safe"
    SAFE = "safe"
    READ_SIGNS = "read_signs"
    HIGH_RISK = "high_risk"
    VERY_HIGH_RISK = "very_high_risk"
    DO_NOT_PARK = "do_not_park"


class ZoneType(StrEnum):
    GENERAL = "general"
    RESIDENT_ONLY = "resident_only"
    PRIVATE_PROPERTY = "private_property"
    COMMERCIAL = "commercial"
    TOWING_HOTSPOT = "towing_hotspot"


class ParkingDecisionOutcome(StrEnum):
    PARK = "PARK"
    CAUTION = "CAUTION"
    DO_NOT_PARK = "DO_NOT_PARK"
    INDETERMINATE = "INDETERMINATE"


class CoverageStatus(StrEnum):
    VERIFIED_COVERAGE = "VERIFIED_COVERAGE"
    NO_VERIFIED_COVERAGE = "NO_VERIFIED_COVERAGE"
    STALE_DATA = "STALE_DATA"
    LOCATION_PRECISION_INSUFFICIENT = "LOCATION_PRECISION_INSUFFICIENT"
    UNVERIFIABLE_SOURCE = "UNVERIFIABLE_SOURCE"
    LOCATION_CONSENT_REQUIRED = "LOCATION_CONSENT_REQUIRED"
    LOCATION_STALE = "LOCATION_STALE"


class ParkingDecisionReasonCode(StrEnum):
    OFFICIAL_RESTRICTION = "OFFICIAL_RESTRICTION"
    RESIDENT_PERMIT_REQUIRED = "RESIDENT_PERMIT_REQUIRED"
    TOWING_RISK = "TOWING_RISK"
    NO_VERIFIED_COVERAGE = "NO_VERIFIED_COVERAGE"
    STALE_DATA = "STALE_DATA"
    LOCATION_PRECISION_INSUFFICIENT = "LOCATION_PRECISION_INSUFFICIENT"
    DECISION_INDETERMINATE = "DECISION_INDETERMINATE"
    UNVERIFIABLE_SOURCE = "UNVERIFIABLE_SOURCE"
    LOCATION_CONSENT_REQUIRED = "LOCATION_CONSENT_REQUIRED"
    LOCATION_STALE = "LOCATION_STALE"
    TEMPORAL_RULE_INDETERMINATE = "TEMPORAL_RULE_INDETERMINATE"


class TemporalRuleEffect(StrEnum):
    PARK = "PARK"
    CAUTION = "CAUTION"
    DO_NOT_PARK = "DO_NOT_PARK"


@dataclass(frozen=True, slots=True)
class TemporalWindow:
    starts_at: time
    ends_at: time


@dataclass(frozen=True, slots=True)
class ParkingTemporalRule:
    """A source-supplied local-time rule; incomplete rules never authorize parking."""

    rule_id: str
    effect: TemporalRuleEffect
    weekdays: tuple[int, ...]
    window: TemporalWindow
    timezone: str
    valid_from: datetime
    valid_until: datetime | None
    exception_dates: tuple[date, ...] = ()
    not_applicable_windows: tuple[TemporalWindow, ...] = ()
    special_restrictions: tuple[str, ...] = ()


def risk_level(score: int) -> RiskLevel:
    if not 0 <= score <= 100:
        raise ValueError("parking score must be between 0 and 100")
    if score >= 90:
        return RiskLevel.VERY_SAFE
    if score >= 75:
        return RiskLevel.SAFE
    if score >= 55:
        return RiskLevel.READ_SIGNS
    if score >= 35:
        return RiskLevel.HIGH_RISK
    if score > 0:
        return RiskLevel.VERY_HIGH_RISK
    return RiskLevel.DO_NOT_PARK


@dataclass(frozen=True, slots=True)
class ParkingZone:
    id: UUID
    name: str
    zone_type: ZoneType
    geometry_geojson: str
    parking_score: int
    provenance: Provenance
    confidence: float
    restriction_summary: str | None
    average_towing_cost_cents: int | None
    towing_hotspot: bool
    observed_at: datetime
    expires_at: datetime | None
    source_id: UUID | None = None
    import_batch_id: UUID | None = None
    jurisdiction: str | None = None
    temporal_rules: tuple[ParkingTemporalRule, ...] = ()
    temporal_schedule_required: bool = False

    @property
    def risk_level(self) -> RiskLevel:
        return risk_level(self.parking_score)


class ParkingZoneRepository(Protocol):
    async def in_viewport(
        self, west: float, south: float, east: float, north: float, limit: int
    ) -> tuple[ParkingZone, ...]: ...

    async def at_location(
        self, longitude: float, latitude: float, *, include_expired: bool = False
    ) -> ParkingZone | None: ...
