"""Versioned parking-assessment contracts and safety invariants."""

from dataclasses import dataclass
from enum import StrEnum

from app.modules.parking.domain import Provenance, RiskLevel, ZoneType, risk_level


class Recommendation(StrEnum):
    PARK = "park"
    CAUTION = "caution"
    DO_NOT_PARK = "do_not_park"


class AssistantIntent(StrEnum):
    PARKING_LEGALITY = "parking_legality"
    SIGN_MEANING = "sign_meaning"
    RESIDENT_PERMIT = "resident_permit"
    TOWING_RISK = "towing_risk"
    TOWING_COST = "towing_cost"
    NEAREST_SAFE_PARKING = "nearest_safe_parking"


@dataclass(frozen=True, slots=True)
class AssessmentContext:
    base_score: int | None
    provenance: Provenance | None
    source_confidence: float | None
    zone_type: ZoneType | None
    towing_hotspot: bool
    restriction_summary: str | None
    average_towing_cost_cents: int | None
    has_resident_permit: bool = False


@dataclass(frozen=True, slots=True)
class ParkingAssessment:
    score: int
    risk_level: RiskLevel
    recommendation: Recommendation
    provenance: Provenance
    confidence: float
    reasons: tuple[str, ...]
    restriction_summary: str | None
    average_towing_cost_cents: int | None
    ruleset_version: str
    prediction_version: str | None
    requires_human_review: bool


def recommendation(score: int) -> Recommendation:
    if score >= 75:
        return Recommendation.PARK
    if score >= 55:
        return Recommendation.CAUTION
    return Recommendation.DO_NOT_PARK


def build_assessment(
    score: int,
    provenance: Provenance,
    confidence: float,
    reasons: tuple[str, ...],
    restriction_summary: str | None,
    average_towing_cost_cents: int | None,
    ruleset_version: str,
    prediction_version: str | None = None,
) -> ParkingAssessment:
    bounded_score = min(max(score, 0), 100)
    return ParkingAssessment(
        score=bounded_score,
        risk_level=risk_level(bounded_score),
        recommendation=recommendation(bounded_score),
        provenance=provenance,
        confidence=min(max(confidence, 0), 1),
        reasons=reasons,
        restriction_summary=restriction_summary,
        average_towing_cost_cents=average_towing_cost_cents,
        ruleset_version=ruleset_version,
        prediction_version=prediction_version,
        requires_human_review=(confidence < 0.5 or provenance is Provenance.ESTIMATED),
    )
