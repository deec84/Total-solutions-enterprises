# Phase 15 — Privacy rights and account lifecycle

## Decision

The architecture promised explicit consent, export, and deletion, but the source only had feature-specific notification consent and media retention. Phase 15 adds a bounded privacy context and a complete mobile flow without claiming legal approval or deploying external infrastructure.

## Delivered

- Append-only decisions for `product_analytics`, `personalized_recommendations`, and `community_research`, each bound to the server-controlled `PARKSHIELD_PRIVACY_POLICY_VERSION`.
- `GET /api/v1/privacy/consents` and `PUT /api/v1/privacy/consents/{purpose}`. Unknown purposes are rejected by the typed contract.
- `POST /api/v1/privacy/export`, which returns a current JSON snapshot with `Cache-Control: private, no-store` and `Pragma: no-cache`.
- `DELETE /api/v1/privacy/account`, protected by the active access token, current password, an explicit deletion confirmation, and a valid TOTP code when MFA is enabled.
- A fail-closed media cleanup port. If a user owns retained community evidence, every object must be confirmed deleted before PostgreSQL removes the account. Missing or failing storage returns `503` and leaves the account intact.
- Migration `0012_privacy_rights` with consent history and data-rights requests. After deletion, the completed request retains only an HMAC subject reference; its user foreign key becomes null.
- Database removal nulls linkable identity audit subjects and uses existing foreign-key cascades for sessions, reports, appeals, reputation, notification preferences, devices, deliveries, and consent history.
- A Flutter privacy center for choices, JSON export/copy, and accessible destructive confirmation. Local credentials are cleared only after the backend returns a real `204`.

## Export minimization

The export includes the account profile, active session metadata, community reports and appeals, reputation, notification preferences, device platform/status, alert delivery status, consent history, data-rights history, and security-event names/timestamps.

It deliberately excludes:

- password hashes;
- encrypted or plaintext MFA secrets;
- refresh/access tokens;
- push token ciphertext and hashes;
- delivery deduplication keys;
- community-media object keys;
- provider credentials and internal subject-reference HMACs.

The API currently produces the export synchronously because the data set is account-scoped and bounded. Before production scale, load tests must confirm the response limit or the implementation must move to an encrypted, expiring asynchronous artifact without weakening authentication or retention.

## Retention and legal boundary

Owned application data is deleted immediately when the transaction succeeds. Community objects are deleted first. The completed deletion-request receipt is retained without a direct user identifier so operations can demonstrate that a request completed without retaining the deleted account.

This is an engineering control, not legal advice. Before production, the owner and qualified counsel must approve:

1. the published policy and `PARKSHIELD_PRIVACY_POLICY_VERSION`;
2. retention periods for security and tamper-evident administrative events;
3. lawful exceptions for fraud, litigation holds, financial records, and municipal contracts;
4. California, Florida, and other applicable jurisdictional request/appeal timelines;
5. processor/subprocessor terms and public contact channels.

Privileged admin/moderator accounts cannot self-delete. They require controlled offboarding to preserve separation of duties and the tamper-evident audit chain.

## API examples without secrets

```http
PUT /api/v1/privacy/consents/product_analytics
Authorization: Bearer <access-token>
Content-Type: application/json

{"granted": false}
```

```http
DELETE /api/v1/privacy/account
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "password": "<current-password>",
  "confirmation": "DELETE MY PARKSHIELD ACCOUNT",
  "mfa_code": "<six-digit-code-if-enabled>"
}
```

Tokens, passwords, and MFA codes must be supplied only by the client at runtime. They must never be placed in shell history, tickets, logs, documentation, or repository files.

## Phase gate

Local source gates require Ruff, strict mypy, Bandit, dependency audit, the complete backend suite at the unchanged 90% minimum, Alembic linear-head/offline SQL, Flutter formatting/analysis/tests at the unchanged 75% minimum, Android debug compilation, repository checks, Terraform validation, IaC scanning, workflow linting, and plist validation.

The implementation run passed 134 backend unit/API tests at 92.62% statement coverage and all 44 Flutter tests at 79.43% line coverage. No threshold was reduced and no test was skipped or marked expected-failure. Exact-commit hosted PostgreSQL/PostGIS migration up/down, integration, backup/restore, dependency audit, container/Compose, CodeQL, Gitleaks, Android, and unsigned iOS checks remain required before the phase gate is approved.

Real staging deletion against the account-owned S3/KMS bucket and legal approval remain external promotion gates. No cloud apply, release, signed artifact, or provider success is claimed.
