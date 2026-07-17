"""Versioned safety evaluation set for the deterministic/predictive boundary."""

import json
from pathlib import Path
from typing import Any

from app.modules.parking.domain import Provenance, ZoneType
from app.modules.parking_ai.domain import AssessmentContext
from app.modules.parking_ai.prediction import BaselinePredictionModel
from app.modules.parking_ai.rules import DeterministicParkingRules


def test_versioned_parking_assistant_evaluation_set() -> None:
    path = Path(__file__).parents[1] / "evaluations" / "parking_assistant_v1.json"
    dataset: dict[str, Any] = json.loads(path.read_text())
    assert dataset["dataset_version"] == "parking-assistant-eval-1.0.0"
    rules = DeterministicParkingRules()
    predictor = BaselinePredictionModel()

    for case in dataset["cases"]:
        zone_type = ZoneType(case["zone_type"]) if case["zone_type"] else None
        context = AssessmentContext(
            base_score=case["base_score"],
            provenance=Provenance.OFFICIAL if case["base_score"] is not None else None,
            source_confidence=1.0 if case["base_score"] is not None else None,
            zone_type=zone_type,
            towing_hotspot=case["hotspot"],
            restriction_summary=None,
            average_towing_cost_cents=None,
            has_resident_permit=case["permit"],
        )
        assessment = rules.evaluate(context) or predictor.predict(context)
        assert assessment.score == case["expected_score"], case["name"]
        assert assessment.provenance.value == case["expected_source"], case["name"]


def test_model_registry_points_to_the_active_evaluation_set() -> None:
    root = Path(__file__).parents[1] / "evaluations"
    registry: dict[str, Any] = json.loads((root / "model_registry.json").read_text())
    versions = registry["active_models"]
    assert versions["parking_rules"]["evaluation_dataset"] == "parking-assistant-eval-1.0.0"
    assert versions["parking_prediction"]["version"] == "parking-baseline-1.0.0"
    assert versions["parking_prediction"]["human_review_below_confidence"] == 0.5
