from itertools import product

from app.modules.parking.domain import Provenance, ZoneType
from app.modules.parking_ai.domain import AssessmentContext, Recommendation
from app.modules.parking_ai.prediction import BaselinePredictionModel
from app.modules.parking_ai.rules import DeterministicParkingRules


def test_official_hard_stops_never_produce_false_safe_recommendation() -> None:
    rules = DeterministicParkingRules()
    for base_score, permit, hotspot in product((0, 20, 60, 100), (False, True), (False, True)):
        private = rules.evaluate(
            AssessmentContext(
                base_score,
                Provenance.OFFICIAL,
                1.0,
                ZoneType.PRIVATE_PROPERTY,
                hotspot,
                "Private parking",
                25000,
                permit,
            )
        )
        assert private is not None
        assert private.score == 0
        assert private.recommendation is Recommendation.DO_NOT_PARK

        resident = rules.evaluate(
            AssessmentContext(
                base_score,
                Provenance.OFFICIAL,
                1.0,
                ZoneType.RESIDENT_ONLY,
                hotspot,
                "Permit required",
                25000,
                False,
            )
        )
        assert resident is not None
        assert resident.score == 10
        assert resident.recommendation is Recommendation.DO_NOT_PARK


def test_prediction_is_invariant_to_absent_demographic_or_geographic_features() -> None:
    # The baseline accepts no demographic, neighborhood, income, race, or ZIP features.
    context = AssessmentContext(None, None, None, None, False, None, None, False)
    predictions = [BaselinePredictionModel().predict(context) for _ in range(100)]
    assert {prediction.score for prediction in predictions} == {50}
    assert {prediction.confidence for prediction in predictions} == {0.35}
    assert all(prediction.requires_human_review for prediction in predictions)
