# ParkShield AI

Production-oriented monorepo for ParkShield AI, a parking-intelligence platform that helps drivers make safer decisions before parking.

## Repository layout

- `backend/`: FastAPI modular monolith and tests.
- `mobile/`: Flutter application using feature-first Clean Architecture.
- `infrastructure/`: deployment and observability assets.
- `docs/`: architecture decisions, product roadmap, and operating guidance.

## Delivery status

Phases 1–15 implement identity, PostGIS risk mapping, explainable Parking AI, sign scanning, community trust, governed media evidence, administration, preventive alerts, towing recovery, nearby recommendations, privacy rights, system qualification, and deployment automation. Production promotion remains deliberately gated on green CI, environment-owned cloud/provider credentials, municipal/map data contracts, legal approval, infrastructure apply evidence, and store signing approval. See `docs/roadmap.md`, `docs/phase-11-deployment.md`, `docs/phase-14-community-media-lifecycle.md`, and `docs/phase-15-privacy-rights.md`.

## Local startup

Prerequisites: Docker with Compose v2. Copy `.env.example` to the ignored
`.env`, replace the local password/JWT placeholders, then run:

```sh
docker compose config --quiet
make up
make verify-stack
```

The API is available at `http://127.0.0.1:8000`, OpenAPI at `/docs`, and
health checks at `/api/v1/health/live` and `/api/v1/health/ready`. Compose runs
Alembic to its single head before starting the API and verifies PostgreSQL with
the PostGIS image.

See `docs/installation.md` for clean-clone, native backend, Flutter, and
troubleshooting instructions. Every accepted setting and secret location is
listed in `docs/environment-variables.md`.

## GitHub and cloud onboarding

The canonical repository is [deec84/Total-solutions-enterprises](https://github.com/deec84/Total-solutions-enterprises). Publication is performed only through explicit, validated Git operations.
Before publishing changes, run:

```sh
make repository-check
make validate
```

The repository check verifies secret/signing/state exclusions, required lock
files and Android Gradle Wrapper tracking, whitespace, and the 50 MB file
boundary using an ephemeral Git index.

- `docs/repository-onboarding.md`: Git initialization, GitHub connection,
  environments/secrets, staging, production, and the ordered owner checklist.
- `docs/external-services.md`: exact accounts, contracts, credentials, and
  currently blocked external tasks.
- `infrastructure/README.md`: Terraform state and AWS stack operation.

## Local quality gates

The prepared macOS ARM64 workspace keeps pinned Python, Flutter, Android/JDK,
Terraform, Trivy, and Actionlint toolchains under the ignored `work/` directory.
Run the complete locally executable gate set with:

```sh
make validate
```

This command runs the isolated authentication regression, the full backend suite
with its unchanged 90% coverage requirement, static/security analysis, Flutter
API/controller/rendering/accessibility tests with a required 75% line-coverage
minimum, an Android debug APK build, Terraform validation, IaC scanning,
workflow linting, and plist validation.
PostGIS/container and iOS builds remain non-optional hosted CI jobs because this
host has neither Docker nor the full Xcode application.

## Engineering rules

- Dependencies point inward: presentation → application → domain; infrastructure implements domain ports.
- Configuration comes from environment variables. Secrets are never committed.
- Every phase must satisfy its exit criteria in `docs/roadmap.md` before the next begins.
- Official data always outranks predictions or community data; provenance is a first-class domain concept.
- A release is promoted by immutable digest and never bypasses migration, security, native-build, or rollback gates.
