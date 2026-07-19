# Production readiness review

## Decision

The application source, migrations, client, CI/CD, infrastructure, and operational controls are implementation-complete for the documented launch scope. Production promotion is **not authorized from this local workspace alone**. It requires green hosted CI plus account-specific cloud, provider, data, signing, and approval evidence.

## Verified locally

- Authentication fixture isolation: 11/11 auth tests pass; one repository graph per test and one shared instance across its requests.
- Backend: 150/150 local unit/API/repository tests; 93.30% coverage with required minimum unchanged at 90%.
- Ruff, strict mypy, and Bandit medium/high pass locally. Exact-commit hosted dependency audit remains mandatory.
- Alembic: one linear head at `0013_municipal_ingestion`; full offline SQL render succeeds.
- Terraform: formatting and provider-schema validation pass with AWS 6.55.0.
- Trivy IaC: zero high/critical findings; no ignored findings.
- Flutter: offline dependency resolution, Dart formatting, Analyze with fatal infos, and all 44 API/controller/rendering/model/accessibility/stop-detection/privacy tests pass; LCOV records 1,444/1,818 executable lines (79.43%) against the enforced 75% minimum.
- Android: Temurin 17, API/target 36, Build Tools 36.0.0, NDK 28.2.13676358, and all SDK licenses are installed; the debug APK builds successfully.
- GitHub workflows: YAML parse and Actionlint 1.7.12 pass; iOS export plist validates.
- Repository onboarding: the ephemeral-index preflight includes dependency locks and the Android Gradle Wrapper, and rejects ignored secrets/signing/state/build paths, high-confidence credential patterns, whitespace errors, and files over 50 MB.
- Container onboarding: `docker-compose.yml` now gates API startup on a successful Alembic head migration against `postgis/postgis:16-3.4-alpine`; a required hosted Compose smoke job verifies readiness, PostGIS, and migration head.
- AWS onboarding: Terraform creates the Route 53 origin alias and emits the exact ECS network JSON consumed by GitHub. Production deployment requires a staging-approved ECR digest and rejects an empty or tag-based image input.
- Community media: the API stores no raw bytes in PostgreSQL, uses SHA-256-verified private S3 objects through the ECS task role, limits retention to 30 days, deletes rejected evidence, issues only short-lived privileged access grants, and audits access/purge operations. Terraform blocks public access, denies insecure transport, applies KMS encryption, version expiry, and least-privilege task permissions.
- Municipal ingestion: the disabled-by-default, MFA-protected boundary accepts only bounded uploaded GeoJSON zones or CSV facilities, records source/batch lineage, uses hash-only quarantine, preserves estimated provenance for synthetic/unapproved sources, and never performs arbitrary outbound fetches. Terraform propagates the disabled feature flag; real activation requires source-rights and staging evidence.

## Mandatory external promotion evidence

1. Hosted quality/CodeQL/infrastructure jobs green for the exact commit, including PostGIS upgrade/downgrade, distributed limiter and facility distance integration, Flutter tests/accessibility, Android APK, unsigned iOS build, container build, backup/restore, and secret scan.
2. Reviewed Terraform plan and apply in isolated staging; smoke journey and SLO observation complete before protected production approval.
3. Contracted HTTPS map, SMTP, push, and municipal tow providers with explicit network ranges and Secrets Manager values.
4. Reviewed municipal/parking-facility data import with provenance, expiry, legal rights, and data-quality ownership.
5. Valid Android/Apple signing custody and successful signed release artifacts before store submission.
6. Staging evidence that the account-owned KMS/S3 policy accepts upload, privileged access, rejection deletion, expiry purge, and noncurrent-version expiration without public exposure.

No CI job is skipped or marked allowed-to-fail to satisfy these gates.

## Remaining local host boundaries

- Docker/PostGIS is not installed, so migrated database integration, image build, backup/restore, and secret-scan jobs require the Linux runner.
- The full Xcode application is not installed, so unsigned and signed iOS builds require the macOS runner. The checked-in project uses Flutter Swift Package Manager integration and does not require CocoaPods.
- The local repository is attached to its GitHub remote, but it is not connected to an AWS account, provider accounts, municipal datasets, or mobile signing identities; hosted deployment evidence and promotion cannot be produced until those environment-owned resources are supplied.
- Docker is unavailable on this host, so the new Compose startup/migration/PostGIS smoke job is validated structurally and by CI configuration but cannot be executed locally.
