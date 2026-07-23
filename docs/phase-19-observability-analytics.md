# Phase 19 — observability and privacy-safe analytics

## Outcome

Phase 19 adds a production-oriented telemetry boundary without connecting an
unapproved monitoring vendor or collecting product data by default. Every
FastAPI application owns an isolated runtime containing metrics, tracing, and
analytics providers. Local/test mode can use bounded in-memory adapters;
disabled adapters make no network calls; configured-but-uninjected external
adapters fail readiness instead of pretending to export.

## Request observability

`SecurityHeadersMiddleware` validates or generates `X-Request-ID`, validates or
derives `X-Correlation-ID`, and continues a valid W3C `traceparent` with a new
server span. The three identifiers are returned to clients and placed in
request-scoped context variables. Access logs are one-line JSON with method,
low-cardinality category, status, and duration. Query strings, raw paths,
headers, bodies, precise locations, and user identifiers are excluded.

The metrics port records:

- request volume, backend errors, and duration;
- authentication, municipal import, sign analysis, Parking Score, community,
  and billing-verification volume by bounded outcome;
- classified external-integration failures;
- accepted and rejected product-event counts.

The trace port has in-memory, disabled, unavailable, and injected
OpenTelemetry-compatible adapters. The source does not import or configure a
vendor SDK. A real SDK tracer must be injected by an approved environment
adapter; selecting `opentelemetry` without that adapter makes `/health/ready`
return 503.

## Product analytics policy

Two independent gates are mandatory: the deployment feature flag and the
user's latest `product_analytics` consent. The mobile controller starts without
consent, learns the persisted decision from the Privacy Center, rejects unknown
or sensitive properties locally, and sends an authenticated allowlisted event
contract only when both gates are on. The server verifies current consent again.

Allowed events are:

- `screen_viewed` (`screen` only);
- `session_started` (`platform`, `app_version`);
- `sign_in_completed` (`outcome`, `mfa_used`);
- `parking_decision_viewed` (`risk_band`, `source_level`);
- `parking_recommendation_opened` (`distance_band`, `price_band`);
- `sign_scan_completed` (`outcome`, `source_level`, `restriction_count`);
- `community_report_submitted` (`report_type`, `outcome`);
- `tow_recovery_searched` (`outcome`, `result_band`);
- `billing_verification_completed` (`provider`, `outcome`).

Passwords, credentials, authorization values, cookies, tokens, receipts,
signed payloads, email, VIN, messages/content, photos, latitude, longitude, and
precise location are prohibited. Unknown fields or nested objects reject the
whole event. The backend replaces the user ID with an independent HMAC
reference, never persists the raw ID in an event, applies 1–90 day retention,
supports expiry purge, and deletes the subject's in-memory events during account
deletion. Account deletion fails closed if the analytics provider cannot confirm
subject deletion. A future durable provider must satisfy the same deletion and
purge port before activation.

## Infrastructure and operations

Terraform creates no monitoring account and performs no apply. It prepares an
independent analytics HMAC secret in Secrets Manager, ECS configuration,
CloudWatch JSON-log metric filters, feature counters, alarms, trace lookup, and
dashboard widgets. `observability/dashboards/parkshield-overview.json` and
`observability/alerts/slo-rules.json` are vendor-neutral contracts validated in
CI. They forbid sensitive dimensions and require golden signals, principal
journeys, SLOs, paging conditions, and runbooks.

External endpoints remain subject to the existing explicit CIDR egress list;
`0.0.0.0/0` is rejected. Integration failures log only provider class,
operation, exception type, and request/correlation/trace identifiers. Exception
messages, provider responses, receipts, device tokens, plates, VIN values, and
credentials are never recorded.

## Gates and remaining external evidence

Required source gates are backend unit/API/regression tests with the unchanged
90% floor, Ruff, strict mypy, Bandit, Flutter format/analyze/tests with the
unchanged 75% floor, observability contract validation, Terraform format/init/
validate, Trivy, workflow lint, repository readiness, hosted CodeQL, PostGIS,
container/Compose, Android, and unsigned iOS builds.

Activation of real export or durable analytics remains blocked on vendor and
data-processing approval, an exact HTTPS collector/sink, restricted network
ranges, environment-owned credentials delivered through Secrets Manager,
sampling/cardinality/cost decisions, a legally approved retention schedule,
staging deletion/retention tests, dashboards receiving real traffic, and an
on-call exercise. No provider success, cloud plan/apply, staging deployment,
production deployment, or release is claimed by this phase.
