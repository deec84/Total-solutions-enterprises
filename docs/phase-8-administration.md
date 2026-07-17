# Phase 8 — Administration

## Delivered

- Role-restricted administrative API and Flutter surface, hidden from standard users.
- RFC 6238 TOTP enrollment and confirmation; a fresh six-digit code is mandatory for overview, moderation, appeals, and audit integrity checks.
- TOTP secrets encrypted at rest with authenticated Fernet encryption; PostgreSQL never receives the plaintext secret.
- Operational overview for users, active sessions, and community-report states.
- Moderation queue with mandatory reasons for approve/reject decisions.
- Appeal uphold/overturn workflow protected by the same privileged policy.
- SHA-256 hash-chained administrative audit trail with PostgreSQL transaction advisory locking, actor, subject, action, time, previous hash, and event hash.
- Audit-integrity API and dashboard signal that detects modified, reordered, or removed records.
- Every administrative mutation implemented here (MFA setup/enable, report moderation, appeal resolution) appends an audit record in the same request transaction.

## Security boundaries

UI role visibility is convenience only. Every privileged backend operation independently validates active account status, role, MFA enrollment, and current TOTP. MFA secrets are excluded from JWTs and normal user responses. Audit writes are serialized across replicas and append-only through the application repository.

## Verification

- Backend unit suite, Ruff, mypy, coverage, and Flutter Analyze are mandatory local gates.
- CI integration verifies migration round trips, encrypted MFA storage, persistent audit records, and chain integrity against PostgreSQL.
- Android, iOS, Flutter test, PostGIS, migration downgrade/upgrade, and backup/restore remain mandatory GitHub Actions gates.
- No tests are skipped and the coverage threshold remains 90%.

## Exit decision

The administration module is complete in source. Final test and coverage totals are recorded by the full gate run.
