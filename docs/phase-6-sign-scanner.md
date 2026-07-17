# Phase 6 — AI parking sign scanner

## Scope delivered

- Authenticated `POST /api/v1/signs/scan` multipart endpoint.
- JPEG, PNG, and WebP validation with a 10 MB and 24 megapixel ceiling.
- In-process Tesseract OCR with English and Spanish language packs; image bytes are not retained.
- Deterministic extraction of no-parking, tow-away, permit/resident, loading, day, and time restrictions.
- Plain-language interpretation, towing-risk score, OCR confidence, and mandatory human-review signal.
- Phone and email redaction before recognized text is returned or logged.
- Flutter camera/gallery workflow with Android lost-data recovery, secure JWT upload, and a non-authoritative safety disclaimer.
- iOS camera and photo-library privacy declarations.

## Security and privacy decisions

Images are decoded and verified before OCR, normalized to RGB, processed in memory, and discarded after the request. Responses use `Cache-Control: no-store`. Unsupported media, malformed images, oversized payloads, and decompression-bomb-sized images are rejected. OCR output is advisory and never overrides official restrictions.

## Verification

- Backend unit suite: 48 passed.
- Sign scanner tests: 6 passed, including redaction, low confidence, corrupt/empty images, authenticated API behavior, and media rejection.
- Backend coverage: 92.58%; the 90% gate remains unchanged.
- Ruff: passed.
- Flutter analyzer: passed with no findings.
- PostgreSQL/PostGIS integration tests are configured in GitHub Actions; they require the CI database service.
- Flutter unit and native builds are configured in GitHub Actions. The prepared ARM64 engine now runs all Flutter tests locally and the Android debug APK builds; the iOS build still requires the macOS runner with full Xcode.

## Exit decision

The source-level and locally executable gates pass, including Flutter tests and Android assembly. PostGIS and iOS gates remain mandatory CI checks; no test is skipped and no threshold is reduced.
