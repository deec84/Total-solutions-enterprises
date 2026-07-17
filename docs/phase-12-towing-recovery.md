# Phase 12 — Towing recovery

## Delivered

- Authenticated POST lookup using state, plate, and optional six-character VIN suffix; identifiers never enter URLs, application logs, database tables, analytics, or caches.
- Contracted municipal-provider port plus authenticated HTTP adapter with bounded timeout, strict response validation, HTTPS navigation, official provenance, confidence, and last-verification time.
- Safe not-found guidance and stable 503 behavior when a provider fails; the application never invents a tow location or directs payment from unverified data.
- Tow company, storage address, phone, hours, required documents, estimated fees, payment methods, source/confidence, call action, and external navigation in Flutter.
- Production fail-fast configuration and Secrets Manager injection for the provider token.

## Gate

Unit and HTTP contract tests cover normalization, invalid identifiers, disabled/degraded providers, contracted response mapping, authentication, privacy notice, and `private, no-store`. Flutter models and static analysis cover both found and not-found states. Native tests/builds remain required CI gates.
