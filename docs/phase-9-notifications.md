# Phase 9 — Preventive alerts and notifications

## Delivered

- Explicit, revocable consent for parking alerts and background location; background access cannot be enabled independently of alerts.
- Preference center with US time-zone selection and quiet hours, including overnight windows.
- Authenticated location-evaluation endpoint using the verified parking-map decision service.
- Warnings only below score 60; missing coverage and safe areas fail silently with an explanatory decision.
- Hour/location/risk deduplication claimed atomically in PostgreSQL before delivery.
- Encrypted device tokens, token hashing for idempotent registration, platform metadata, and delivery outcome records.
- Push-provider port plus authenticated HTTP gateway adapter; absent production configuration fails closed.
- Flutter location stream with a privacy-local parking-stop detector: automotive movement arms detection, a stable low-speed cluster with acceptable GPS accuracy triggers one evaluation, and another driving segment is required before re-arming.
- Android uses a 15-second/10-meter foreground location stream; iOS uses automotive background-location settings; both deliver local high-priority notifications only after a likely stop.
- Android background/foreground location and notification permissions; iOS Always location purpose and Location Updates background mode.
- Automatic resume after app startup only when persisted consent and OS `Always` permission are both present.

## Privacy and safety

Location monitoring starts only after the user enables the feature and grants OS-level Always permission. If permission is not granted, server consent is rolled back. Disabling alerts cancels the stream. Device tokens are authenticated-encrypted at rest and never logged. The server applies consent, quiet hours, safety threshold, and deduplication even if a client is modified.

## Verification

- Unit tests cover consent invariants, unknown time zones, quiet hours across midnight, safe/uncovered areas, high-risk delivery, device registration, duplicate suppression, stop arming/dwell/re-arm behavior, poor accuracy, GPS drift, and missing platform speed.
- HTTP contract tests cover preference update, device registration, and automatic location evaluation.
- PostgreSQL CI integration covers preference persistence, encrypted device tokens, decryption, and atomic duplicate claims.
- Ruff, mypy, Flutter Analyze, backend coverage ≥90%, mobile line coverage ≥75%, Android build, iOS build, and Flutter tests remain mandatory gates.

## Exit decision

The notification module is complete in source. The aggregate mobile suite passes 40/40 tests at 77.61% line coverage, including five deterministic parking-stop cases; the backend suite passes 122/122 at 91.78% coverage against the unchanged 90% requirement. No test is skipped.
