"""Assistant orchestration with deterministic-before-predictive precedence."""

import logging

from app.modules.parking.domain import ParkingZone
from app.modules.parking.service import ParkingMapService
from app.modules.parking_ai.domain import AssessmentContext, ParkingAssessment
from app.modules.parking_ai.prediction import BaselinePredictionModel
from app.modules.parking_ai.rules import DeterministicParkingRules

logger = logging.getLogger(__name__)


class ParkingAssistantService:
    def __init__(
        self,
        map_service: ParkingMapService,
        rules: DeterministicParkingRules,
        predictor: BaselinePredictionModel,
    ) -> None:
        self._map_service = map_service
        self._rules = rules
        self._predictor = predictor

    async def assess(
        self, longitude: float, latitude: float, has_resident_permit: bool = False
    ) -> ParkingAssessment:
        zone = await self._map_service.decision(longitude, latitude)
        context = self._context(zone, has_resident_permit)
        deterministic = self._rules.evaluate(context)
        assessment = (
            deterministic if deterministic is not None else self._predictor.predict(context)
        )
        logger.info(
            "parking_assessment score=%s provenance=%s ruleset=%s prediction=%s review=%s",
            assessment.score,
            assessment.provenance.value,
            assessment.ruleset_version,
            assessment.prediction_version,
            assessment.requires_human_review,
        )
        return assessment

    @staticmethod
    def _context(zone: ParkingZone | None, has_resident_permit: bool) -> AssessmentContext:
        if zone is None:
            return AssessmentContext(None, None, None, None, False, None, None)
        return AssessmentContext(
            base_score=zone.parking_score,
            provenance=zone.provenance,
            source_confidence=zone.confidence,
            zone_type=zone.zone_type,
            towing_hotspot=zone.towing_hotspot,
            restriction_summary=zone.restriction_summary,
            average_towing_cost_cents=zone.average_towing_cost_cents,
            has_resident_permit=has_resident_permit,
        )
