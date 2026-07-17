"""Deterministic parking rules that always outrank statistical predictions."""

from app.modules.parking.domain import Provenance, ZoneType
from app.modules.parking_ai.domain import AssessmentContext, ParkingAssessment, build_assessment

RULESET_VERSION = "parking-rules-2026-07-01"


class DeterministicParkingRules:
    def evaluate(self, context: AssessmentContext) -> ParkingAssessment | None:
        if context.zone_type is ZoneType.PRIVATE_PROPERTY:
            return self._official_stop(
                context, "Private property requires explicit owner permission."
            )
        if context.zone_type is ZoneType.RESIDENT_ONLY and not context.has_resident_permit:
            return build_assessment(
                10,
                context.provenance or Provenance.ESTIMATED,
                context.source_confidence or 0.5,
                ("A resident permit is required and none was provided.",),
                context.restriction_summary,
                context.average_towing_cost_cents,
                RULESET_VERSION,
            )
        if context.base_score is None:
            return None

        score = context.base_score
        reasons: list[str] = ["The score starts from the best available zone evidence."]
        if context.towing_hotspot:
            score = min(score, 20)
            reasons.append("This location is a known towing hotspot.")
        if context.zone_type is ZoneType.TOWING_HOTSPOT:
            score = min(score, 20)
            reasons.append("The zone is classified as a towing hotspot.")
        if context.zone_type is ZoneType.RESIDENT_ONLY and context.has_resident_permit:
            reasons.append("A resident permit was provided; posted conditions still apply.")
        return build_assessment(
            score,
            context.provenance or Provenance.ESTIMATED,
            context.source_confidence or 0.5,
            tuple(reasons),
            context.restriction_summary,
            context.average_towing_cost_cents,
            RULESET_VERSION,
        )

    def _official_stop(self, context: AssessmentContext, reason: str) -> ParkingAssessment:
        provenance = context.provenance or Provenance.ESTIMATED
        return build_assessment(
            0,
            provenance,
            context.source_confidence or 0.5,
            (reason,),
            context.restriction_summary,
            context.average_towing_cost_cents,
            RULESET_VERSION,
        )
