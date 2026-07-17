# Production readiness review

## Decision

The application source, migrations, client, CI/CD, infrastructure, and operational controls are implementation-complete for the documented launch scope. Production promotion is **not authorized from this local workspace alone**. It requires green hosted CI plus account-specific cloud, provider, data, signing, and approval evidence.

## Verified locally

- Authentication fixture isolation: 11/11 auth tests pass; one repository graph per test and one shared instance across its requests.
- Backend: 106/106 tests; 91.45% coverage with required minimum unchanged at 90%.
- Ruff, strict mypy, Bandit medium/high, and pip-audit: pass; no known audited dependency vulnerabilities.
- Alembic: one linear head at `0009_distributed_login_limits`; full offline SQL render succeeds.
- Terraform: formatting and provider-schema validation pass with AWS 6.55.0.
- Trivy IaC: zero high/critical findings; no ignored findings.
- Flutter: dependency resolution, Dart formatting, Analyze with fatal infos, and all 40 API/controller/rendering/model/accessibility/stop-detection tests pass; LCOV records 1,262/1,626 executable lines (77.61%) against the enforced 75% minimum.
- Android: Temurin 17, API/target 36, Build Tools 36.0.0, NDK 28.2.13676358, and all SDK licenses are installed; the debug APK builds successfully.
- GitHub workflows: YAML parse and Actionlint 1.7.12 pass; iOS export plist validates.
- Repository onboarding: the ephemeral-index preflight tracks 301 intended files, includes dependency locks and the Android Gradle Wrapper, and rejects ignored secrets/signing/state/build paths, high-confidence credential patterns, whitespace errors, and files over 50 MB.
- Container onboarding: `docker-compose.yml` now gates API startup on a successful Alembic head migration against `postgis/postgis:16-3.4-alpine`; a required hosted Compose smoke job verifies readiness, PostGIS, and migration head.
- AWS onboarding: Terraform creates the Route 53 origin alias and emits the exact ECS network JSON consumed by GitHub. Production deployment requires a staging-approved ECR digest and rejects an empty or tag-based image input.

## Mandatory external promotion evidence

1. Hosted quality/CodeQL/infrastructure jobs green for the exact commit, including PostGIS upgrade/downgrade, distributed limiter and facility distance integration, Flutter tests/accessibility, Android APK, unsigned iOS build, container build, backup/restore, and secret scan.
2. Reviewed Terraform plan and apply in isolated staging; smoke journey and SLO observation complete before protected production approval.
3. Contracted HTTPS map, SMTP, push, and municipal tow providers with explicit network ranges and Secrets Manager values.
4. Reviewed municipal/parking-facility data import with provenance, expiry, legal rights, and data-quality ownership.
5. Valid Android/Apple signing custody and successful signed release artifacts before store submission.

No CI job is skipped or marked allowed-to-fail to satisfy these gates.

## Remaining local host boundaries

- Docker/PostGIS is not installed, so migrated database integration, image build, backup/restore, and secret-scan jobs require the Linux runner.
- The full Xcode application is not installed, so unsigned and signed iOS builds require the macOS runner. The checked-in project uses Flutter Swift Package Manager integration and does not require CocoaPods.
- The local repository is attached to its GitHub remote, but it is not connected to an AWS account, provider accounts, municipal datasets, or mobile signing identities; hosted deployment evidence and promotion cannot be produced until those environment-owned resources are supplied.
- Docker is unavailable on this host, so the new Compose startup/migration/PostGIS smoke job is validated structurally and by CI configuration but cannot be executed locally.
