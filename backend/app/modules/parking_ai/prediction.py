"""Calibratable baseline used only when deterministic verified evidence is absent."""

from dataclasses import dataclass

from app.modules.parking.domain import Provenance
from app.modules.parking_ai.domain import AssessmentContext, ParkingAssessment, build_assessment
from app.modules.parking_ai.rules import RULESET_VERSION


@dataclass(frozen=True, slots=True)
class BaselinePredictionModel:
    version: str = "parking-baseline-1.0.0"

    def predict(self, context: AssessmentContext) -> ParkingAssessment:
        score = 50
        reasons = ["No verified zone covers this location; this is a conservative estimate."]
        if context.towing_hotspot:
            score = 20
            reasons.append("Historical signals indicate elevated towing activity.")
        return build_assessment(
            score,
            Provenance.AI_PREDICTION,
            0.35,
            tuple(reasons),
            context.restriction_summary,
            context.average_towing_cost_cents,
            RULESET_VERSION,
            self.version,
        )
