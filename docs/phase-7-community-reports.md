# Phase 7 — Community intelligence

## Delivered

- Authenticated JSON and multipart report submission for towing, restriction, price, and sign observations.
- Location, length, media type, 10 MB, 24 MP, and image-decode validation.
- SHA-256 media evidence fingerprinting without retaining raw image bytes in the API database.
- Deterministic evidence score with conservative auto-publication; ambiguous reports enter moderation.
- 24-hour duplicate detection using normalized content and rounded coordinates.
- Moderator/admin queue plus approve/reject actions protected by deny-by-default RBAC.
- Reporter reputation updated only after moderator decisions.
- Owner-only, single-open-appeal workflow with uphold/overturn resolution.
- Thirty-day report expiry and provenance metadata.
- Flutter report form using the current map center, secure access token, optional camera evidence, and clear review state.

Raw community photos are transient in this phase: the database stores only their evidence hash. Durable media retention must use an approved encrypted object-store adapter with deletion policy; retaining ungoverned user media is intentionally prohibited.

## Verification

- Backend: 58 tests passed.
- Ruff and mypy: passed.
- Coverage: 90.30%; the required threshold remains 90%.
- Flutter Analyze: passed.
- PostgreSQL integration coverage includes report persistence, moderation, reputation, appeal, cascade deletion, and migration upgrade/downgrade in GitHub Actions.
- Flutter unit/native Android/iOS gates remain mandatory GitHub Actions jobs for exact-commit evidence. Flutter tests and the Android debug build also pass locally with the prepared ARM64 toolchain; iOS requires the macOS runner with full Xcode.

## Exit decision

The module is functionally complete for privacy-preserving text reports and transient photo evidence. No test was skipped and no quality threshold was reduced.
