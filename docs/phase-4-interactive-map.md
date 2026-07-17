# Phase 4: Interactive map

## Implemented vertical slice

- Parking Score semantics from 0–100 with six explicit risk bands.
- Mandatory provenance (`official`, `community_verified`, `ai_prediction`, `estimated`) and confidence from 0–1.
- PostGIS polygon schema with score/confidence/cost constraints and GiST viewport index.
- Authenticated REST viewport query with bounded results, expiry filtering, and GeoJSON output.
- Flutter interactive map using `flutter_map`, configurable HTTPS tile source, debounced viewport loading, polygon overlays, score labels, risk colors, attribution, loading state, and degraded error state.
- Zone classifications for general, resident-only, private, commercial, and towing-hotspot areas.
- Point decision API using `ST_Covers` with deterministic source precedence: official, community verified, AI prediction, then estimated.
- Mobile “Can I park here?” action at map center with a decision sheet showing score, risk, source, confidence, restrictions, towing-hotspot warning, and estimated towing cost.
- Backend domain/API tests and Flutter GeoJSON parsing test.

Current local gate: 35 backend tests pass at 93.03% coverage; Ruff, strict mypy, Alembic offline render, Dart formatting, and Flutter Analyze pass. PostGIS migration/round-trip now covers viewport and point decisions in required GitHub Actions; native builds remain required there.

## Phase gate

Phase 4 is approved locally: all 35 backend tests pass with 93.05% coverage; Ruff, strict mypy, migration rendering, Dart formatting, and Flutter Analyze pass. Viewport responses use short private caching with `Vary: Authorization`; point safety decisions use `no-store`. Flutter exposes type filters for general, resident-only, private, commercial, and towing-hotspot layers. Historical/community report layers are populated by Phase 7 while preserving this map contract.
