# Phase 10 — System qualification

## Automated qualification matrix

| Area | Gate |
|---|---|
| Unit and contracts | Backend unit suite, strict Pydantic contracts, unique OpenAPI operation IDs, protected-operation bearer declarations |
| Cross-feature | Migrated PostgreSQL journey: registration, verification, login, geospatial decision, Parking AI, alert consent/evaluation, and community report |
| Database | Alembic upgrade, full downgrade and re-upgrade, SQL repositories, PostGIS queries, encrypted fields, uniqueness and cascade behavior |
| Mobile | Flutter Analyze with fatal infos, authenticated HTTP contracts, model/controller/widget tests, feature-page success/degraded paths, accessibility contrast, Android target-size guidelines, and line coverage ≥75% |
| Native | Android debug APK and unsigned iOS debug build on native GitHub runners |
| Load | 200 concurrent ASGI liveness requests with a five-second upper bound; production load profiles remain environment-specific |
| Chaos/degraded | Database readiness failure returns stable 503; missing parking evidence, disabled push, denied location, and OCR corruption fail closed |
| Security | Ruff, strict mypy, Bandit medium/high gate, pip-audit with zero known dependency vulnerabilities, Gitleaks, weekly CodeQL extended analysis |
| Privacy | No password/MFA fields in OpenAPI, encrypted MFA and push tokens, non-retained images, explicit/revocable background consent |
| AI safety/fairness | Versioned evaluation dataset, exhaustive official hard-stop invariants, zero false-safe hard stops, no demographic/ZIP/income features, deterministic baseline stability |
| Recovery | PostgreSQL backup, restore into a new database, schema revision verification, and documented PITR runbook |
| Supply chain | Dependabot for Python, Dart, Docker, and GitHub Actions; container built non-root/read-only |

## Security remediation

The qualification audit found vulnerable versions of `cryptography` and `pytest`. They were upgraded to the fixed release ranges (`cryptography >=48.0.1,<49` and `pytest >=9.0.3,<10`) and pip-audit then reported no known vulnerabilities. No advisory was ignored.

## Current evidence and environment limitation

All locally executable backend gates pass. The Flutter cache now uses native ARM64 engine artifacts, so all 40 API/controller/rendering/model/accessibility/stop-detection tests execute locally and produce LCOV. The local Android toolchain uses Temurin 17, API/target 36, Build Tools 36.0.0, and NDK 28.2.13676358; `flutter build apk --debug` succeeds. Docker/PostGIS and the full Xcode application remain unavailable, so database/container and iOS jobs stay mandatory in GitHub Actions; they are not skipped or marked allowed-to-fail.

## Exit decision

System-wide qualification is implemented as reproducible gates. The final local backend run collected 106 tests: 106 passed with 91.45% statement coverage against an unchanged 90% threshold. The mobile run collected 40 tests: 40 passed, including authenticated feature-client contracts, feature-page success/degraded paths, accessibility, and parking-stop detection; LCOV measured 1,262/1,626 executable lines (77.61%) against the enforced 75% minimum. Ruff, strict mypy, Bandit medium/high, pip-audit, Terraform validation, Trivy high/critical IaC scanning, Flutter Analyze, Android debug assembly, workflow lint, and plist validation pass. Hosted PostGIS, container, iOS, CodeQL, Gitleaks, backup/restore, and cloud promotion gates must still be green for the exact commit before production promotion.
