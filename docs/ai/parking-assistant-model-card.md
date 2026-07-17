# Parking Assistant baseline model card

## Purpose and version

`parking-baseline-1.0.0` provides a conservative fallback only when no verified parking zone covers a location. `parking-rules-2026-07-01` executes first and cannot be overridden by this model.

## Inputs and outputs

Inputs are structured zone evidence, source provenance/confidence, zone classification, towing-hotspot status, restriction summary, estimated towing cost, and whether the user reports a relevant resident permit. Outputs include score, risk band, recommendation, confidence, reasons, provenance, and version identifiers.

## Safety policy

- Official private-property restrictions produce score 0.
- Missing resident permits produce a do-not-park recommendation.
- Towing hotspots cap the score at 20.
- Missing verified data produces score 50 with 0.35 confidence and a read-signs/do-not-assume explanation.
- Every user-facing result includes a current-signs disclaimer.
- Model output never replaces or silently edits official evidence.

## Evaluation and release gate

The versioned dataset `backend/evaluations/parking_assistant_v1.json` must pass exactly in CI. Future statistical models require calibration error, false-safe rate, geographic slice, provenance precedence, drift, latency, and rollback gates. A release fails if any official hard-stop case receives a recommendation other than `do_not_park`; the false-safe target for the curated safety set is zero.

## Limitations

The baseline does not infer municipal law, availability, weather, temporary events, or sign text. It is not legal advice. Geographic expansion requires official ingestion and city-specific evaluation sets before enabling confident recommendations.
