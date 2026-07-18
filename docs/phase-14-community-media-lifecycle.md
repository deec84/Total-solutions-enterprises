# Phase 14 — Community media lifecycle

## Decision

The documented phases 1–13 were implementation-complete. The next explicit source-level gap was the reserved but unused `PARKSHIELD_MEDIA_BUCKET`: Phase 7 intentionally discarded raw community photos until an approved encrypted adapter and deletion policy existed. Phase 14 closes that gap without authorizing cloud deployment.

## Delivered

- A domain-owned `CommunityMediaStore` port and lifecycle service; community application code does not depend on AWS.
- A private S3 adapter using the ECS task role, bucket-default KMS encryption, SHA-256 upload checksum, integrity/retention metadata, `private, no-store`, and no public object URLs.
- Migration `0011_community_media_lifecycle` for object metadata, content type, bounded size, retention deadline, deletion timestamp, constraints, and purge index. Raw media never enters PostgreSQL.
- One deterministic key per report/checksum. Object keys are internal and excluded from API responses.
- Fail-closed deployed configuration: staging/production require a media bucket; local/test mode remains hash-only and retains no raw bytes when storage is absent.
- Immediate object deletion when moderation rejects a report. A failed report write attempts compensating object deletion.
- Bounded, retryable administrative purge for expired objects; successful deletions are marked transactionally and failures remain eligible for retry.
- Privileged access grants expire in 30–300 seconds, responses are non-cacheable, and every access/purge action enters the tamper-evident administrative audit chain.
- Terraform denies insecure S3 transport, blocks all public access, enables versioning and KMS encryption, expires current objects after 30 days and noncurrent versions after 7 days, and grants only object/KMS operations to the ECS task role.

## Privacy and failure behavior

The public report contract exposes only the evidence hash, availability flag, retention deadline, and deletion time. It never exposes an object key. Storage, deletion, or signing failures produce stable fail-closed behavior; no provider exception or credential reaches a client. Rejected or expired evidence cannot receive a new access grant.

Local placeholders are not cloud credentials. No staging/production object was created, no Terraform apply was run, and no release was produced.

## Phase gate

Required local evidence: repository readiness, Ruff, strict mypy, Bandit, dependency audit, full backend coverage at the unchanged 90% minimum, Alembic linear-head/offline SQL, Flutter analysis/tests at the unchanged 75% minimum, Android debug build, Terraform validation, Trivy, Actionlint, and plist validation.

The completed local gate collected 122 backend tests: 122 passed with 91.84% statement coverage against the unchanged 90% threshold. All 40 Flutter tests passed with 77.61% line coverage against the unchanged 75% threshold, and the Android debug APK built successfully. Repository readiness, Ruff, strict mypy, Bandit, pip-audit, Alembic head/offline SQL, Terraform format/validation, Trivy, Actionlint, and plist validation also passed. No test was skipped, marked expected-failure, or allowed to fail.

Required hosted evidence for the exact PR commit: PostgreSQL/PostGIS upgrade/downgrade and integration suite, backup/restore, container/Compose, Gitleaks, CodeQL, Android, and unsigned iOS. Account-owned S3/KMS behavior remains an external staging gate and must not be simulated as a deployment.
