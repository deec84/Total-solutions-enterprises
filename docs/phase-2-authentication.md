# Phase 2 — Authentication

## Delivered

Normalized registration, Argon2 password hashing, verified email, JWT access tokens, single-use rotating refresh families, logout/session revocation, password recovery, user/moderator/admin RBAC, admin MFA, non-enumerating errors, structured audit events, SMTP delivery, and Flutter Keychain/Keystore-backed auth flows are implemented.

Production users, sessions, audit events, encrypted MFA secrets, and login abuse state persist in PostgreSQL. The login limiter uses an atomic upsert shared by every ECS replica, returns `429` with `Retry-After`, resets on successful authentication, and removes stale state. In-memory adapters are limited to isolated tests/local service graphs.

## Fixture isolation correction

The modified fixture is `api` in `backend/tests/test_auth.py`, supported by the function-scoped `identity_service` fixture. Pytest's default function scope creates one isolated `IdentityService` and repository graph per test. The `api` fixture installs that exact service as FastAPI's `get_identity_service` override for every request in the test, then clears the override during teardown.

The defect occurred because the old override factory built a new service and new in-memory repositories on every request. Registration wrote the user into one instance; verification/login then read a different empty instance. Sharing the single function-scoped service preserves data across requests inside one test, while a new fixture instance for the next test prevents cross-test leakage.

After the correction, all 11 registration/login/session contract tests pass. The final full backend run passes 106/106 tests with 91.45% coverage against the unchanged 90% minimum. No test is skipped, expected-failure, or allowed to fail.

## HTTP contracts

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/verify-email`
- `POST /api/v1/auth/password-reset/request`
- `POST /api/v1/auth/password-reset/confirm`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/sessions`
- `DELETE /api/v1/auth/sessions/{session_id}`

Access tokens expire after 15 minutes by default; refresh tokens expire after 30 days and rotate on every use. Verification/reset tokens are signed, purpose-limited, expiring, and single-use where applicable. Staging/production fail startup if JWT, TLS database, SMTP, push, or tow-provider configuration is unsafe or incomplete.

## Gate

The authentication phase is approved in source and local verification. All 40 Flutter tests pass under the new 75% mobile line-coverage gate, and the Android debug build passes locally. PostgreSQL migration/integration and the iOS build remain mandatory GitHub Actions gates because this host lacks Docker/PostGIS and the full Xcode application.
