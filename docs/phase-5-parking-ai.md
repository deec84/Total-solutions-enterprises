# Phase 5: Parking AI

## Implemented

- Versioned assessment contract with score, risk band, recommendation, provenance, confidence, reasons, ruleset/model versions, costs, restrictions, and human-review flag.
- Deterministic rules execute before prediction and hard-stop private property, missing resident permits, and towing hotspots.
- Conservative baseline model for missing verified data: score 50, confidence 0.35, explicit AI provenance, and mandatory review/sign-reading guidance.
- Authenticated, non-cacheable parking-assistant API.
- Versioned safety evaluation dataset and model registry validated in the test suite.
- Structured monitoring logs omit coordinates, questions, tokens, and user identifiers.
- Model card documents intended use, limitations, zero false-safe requirement for official hard stops, and future calibration/drift gates.
- Flutter assistant UI uses the current map center, exposes permit context, reasons, source/confidence, disclaimer, and low-confidence escalation.
- Evidence-bound intent handling distinguishes legality, sign meaning, resident permits, towing risk/cost, and nearby-safe-parking requests instead of ignoring the user's question.

## Gate

Phase 5 was approved at its phase gate with 42 backend tests and 93.65% coverage. The current aggregate qualification is stronger: 105/105 backend tests at 91.33% coverage, 40/40 Flutter tests at 77.61% line coverage, and the Android debug build pass. The versioned evaluation set still passes exactly. PostGIS integration and iOS remain required GitHub Actions gates.

Future learned models may replace the conservative predictor only after offline calibration, geographic slicing, false-safe evaluation, shadow deployment, monitoring, and rollback approval. They cannot replace the deterministic official-data layer.
