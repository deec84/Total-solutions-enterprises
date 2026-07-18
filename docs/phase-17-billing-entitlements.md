# Phase 17 — Billing entitlements and store-verification foundation

## Outcome

ParkShield has a provider-neutral, fail-closed foundation for premium membership without charging anyone or claiming that an unverified receipt succeeded. The source supports product discovery, current entitlement status, server verification, restore reconciliation, privacy export, and account unlinking. Billing is disabled in every example environment and the production Flutter build uses a disabled native-store bridge until the owner completes the external gates.

## Trust model

- A client never sends `active`, an expiry, or an entitlement. It sends only platform, approved product ID, and opaque signed evidence.
- The backend sends that evidence to one preconfigured HTTPS verification gateway using a dedicated bearer token. The endpoint cannot contain credentials, query strings, or fragments and is not selected by the client.
- The gateway response is strictly typed and must bind the verified user, platform, product, entitlement, status, environment, timestamps, transaction, and event.
- The requested user/product must match the verified evidence. Timezones and subscription chronology are mandatory.
- Production accepts only production store evidence; local, test, and staging environments accept only sandbox evidence.
- Unknown products, malformed payloads, provider failures, stale events, revoked purchases, and disabled configuration never grant premium access.
- Prices, currency, introductory offers, taxes, renewal terms, and refund terms come from App Store or Google Play. The backend deliberately has no price field.

## Data minimization and lifecycle

Raw receipts, signed payloads, provider bearer tokens, store transaction IDs, and original transaction IDs are never written to PostgreSQL or API responses. The ledger stores HMAC-SHA-256 references under an independent environment key, product/platform/status, sandbox/production marker, purchase/expiry/verification times, and renewal state.

The latest verified record supplies current entitlement; event references are append-only and idempotent. Older verified events may be retained as evidence but cannot overwrite newer state. Expired, paused, or revoked records resolve to the free tier.

Account deletion sets the subscription's user foreign key to null. It does not cancel Apple/Google billing. The user must cancel through the store, and the UI says so before deletion. Pseudonymous billing evidence remains for reconciliation and any legally approved financial retention period; the final duration and deletion exceptions require owner/legal approval. Privacy export includes human-meaningful subscription fields but excludes every HMAC/store reference.

## API

All endpoints require an authenticated ParkShield session and return `Cache-Control: private, no-store`.

| Method and path | Behavior |
|---|---|
| `GET /api/v1/billing/configuration` | Returns enabled state, public product IDs, entitlements, and `app_store_or_google_play` as pricing authority. |
| `GET /api/v1/billing/entitlement` | Returns free/premium, status, platform, product, expiry, renewal, and last verification. |
| `POST /api/v1/billing/purchases/verify` | Verifies opaque signed store evidence and reconciles the ledger; returns 503 while disabled/unavailable. |

The signed payload is limited to 128 KiB. The response never echoes it.

## Mobile boundary

The membership page shows current server-authoritative status, warns when billing is disabled, and explains separate store cancellation. A `StorePurchaseBridge` port owns purchase and restore operations. The checked-in runtime adapter is deliberately disabled, so no charge can be initiated. Synthetic tests inject a fake bridge solely to prove that evidence still requires backend verification.

Do not replace the disabled bridge until the owner selects the official Flutter/native purchase library, accepts both store agreements, creates products, approves pricing/terms, supplies sandbox accounts through approved systems, and approves the verification/notification architecture. Native code must use the ParkShield user UUID as the store account token/obfuscated account ID so server events bind to the correct account.

## Configuration and infrastructure

`PARKSHIELD_BILLING_ENABLED=false` is the default. Terraform always generates the independent billing-subject HMAC secret and grants ECS read access only to that secret. Gateway token access and ECS injection are conditional on `billing_enabled`. Terraform rejects enabled billing unless an HTTPS gateway, Secrets Manager token ARN, and at least one product ID are present. Existing provider egress CIDRs must include the exact gateway range; unrestricted internet remains prohibited.

No Terraform apply, product creation, payment agreement, provider credential, real store payload, signed release, or deployment is performed by this phase.

## Contract and quality gates

Synthetic contract tests cover disabled/error states, strict gateway responses, user/product binding, timestamp validation, HMAC minimization, event idempotency, stale updates, API no-store behavior, privacy export, SQL upsert mapping, account-deletion unlinking on real PostgreSQL, Flutter API parsing, purchase/restore UI, and fail-closed rendering. The phase also requires the unchanged backend/mobile coverage thresholds, migration up/down, dependency/security scans, PostGIS/container/Compose, Android/iOS builds, Terraform/Trivy, CodeQL, and Gitleaks for the exact commit.

## Owner activation checklist

1. Decide premium features, products, billing periods, trial/intro offers, prices by market, refund policy, family sharing, grace period, account-transfer policy, and fleet-versus-consumer strategy.
2. Obtain finance/tax/legal approval and accept Apple/Google paid-application agreements. This creates real contractual and financial obligations.
3. Create App Store Connect and Google Play products; record exact IDs without credentials.
4. Select and security-review the native Flutter purchase library and the server verification/notification implementation.
5. Create gateway credentials and store verification identities through organization-controlled consoles; store them only in Secrets Manager/workload identity.
6. Restrict gateway DNS/CIDRs, TLS, rate limits, logs, DPA, receipt retention, and incident contacts. Never log raw receipts.
7. Connect native purchase/restore adapters and store account tokens in a new reviewed phase with contract tests.
8. Test sandbox purchase, renewal, expiration, grace, pause, refund, revocation, restore, replay, account mismatch, outage, and notification ordering.
9. Review privacy export/deletion behavior and approve the financial-record retention schedule.
10. Obtain explicit staging and release authorization. Production, signed artifacts, and store submissions remain blocked.
