# Delivery roadmap and phase gates

Each module is implemented, locally verified where the environment permits, tested, and documented before the next. When a native/cloud tool is unavailable locally, its required non-optional CI gate is configured before implementation continues; production promotion still requires every hosted and staging gate to pass.

## 1. Project structure — implemented

Deliverables: monorepo, API/mobile shells, local PostgreSQL, container hardening baseline, architecture and quality gates. Exit: API tests, lint/type checks, Flutter analysis/tests, image build, Compose health check, and secret scan pass.

## 2. Authentication — implemented; native CI gate required

Email/phone identity, secure password hashing, verified contact flow, rotating refresh-token families, session revocation, recovery, RBAC, rate limiting, and audit events. Exit: abuse and authorization matrix tests pass.

## 3. Database — implemented; PostGIS CI gate required

PostgreSQL/PostGIS schema, Alembic migrations, repository/unit-of-work implementations, data classification, seed strategy, backup/PITR and restore drill. Exit: migration up/down tests and repository integration tests pass.

## 4. Interactive map — implemented; geospatial CI gate required

Viewport/geospatial APIs, map provider abstraction, clustering, cached tiles/aggregates, risk legend, accessibility, and degraded/offline behavior.

## 5. Parking AI — implemented; evaluation/native CI gates required

Versioned score contract and provenance, deterministic rules engine, feature pipeline, calibrated baseline model, evaluation sets, model registry, monitoring, human escalation, and explanations.

## 6. Sign scanner — implemented; native/PostGIS CI gates required

Consent-aware upload, malware/content validation, PII redaction, OCR, structured regulation extraction, translation, confidence thresholds, human review, retention and deletion.

## 7. Community reports — implemented; PostGIS/native CI gates required

Media/report submission, duplicate and fraud detection, reputation, moderation queue, appeals, provenance and expiry, safety controls.

## 8. Administration — implemented; PostgreSQL/native CI gates required

Separate privileged surface, least-privilege roles, MFA requirement, moderation and data-quality workflows, tamper-evident audit trail.

## 9. Notifications — implemented; PostgreSQL/native CI gates required

Explicit consent, geofencing and background-location controls, deduplication, quiet hours, push provider abstraction, preference center, delivery observability.

## 10. Testing — implemented; native/PostGIS/security CI gates required

Cross-feature contract, integration, end-to-end, accessibility, load, chaos, security, privacy, AI quality/fairness, and disaster-recovery suites. Testing starts in Phase 1; this phase completes system-wide qualification.

## 11. Deployment — implemented; cloud/native promotion gates required

Infrastructure as code, ephemeral environments, staged rollouts, migrations, autoscaling, CDN/WAF, centralized secrets, SLO dashboards, alerting, runbooks, incident response, rollback and production readiness review.

## 12. Towing recovery — implemented; provider/native CI gates required

Privacy-safe tow lookup provider abstraction, impound details, required documents, fee estimates, hours, payment methods, navigation, no-store APIs, and mobile recovery flow.

## 13. Parking recommendations — implemented; PostGIS/native CI gates required

Nearby alternatives ranked by walk distance, safety, price, historical towing frequency, ratings, and availability with explicit provenance and degraded-data behavior.

## 14. Community media lifecycle — implemented; object-store/cloud gate required

Private KMS-encrypted evidence storage, integrity metadata, bounded retention, privileged short-lived access, immediate logical deletion after rejection, retryable expiry purge, audit events, and fail-closed deployed configuration. Exit: lifecycle, API, adapter, migration, security, and infrastructure gates pass without real cloud credentials; an account-owned staging apply and object-store exercise remain mandatory before promotion.

## 15. Privacy rights and account lifecycle — implemented; hosted/legal gates required

Append-only optional-consent history, data-minimized JSON export, password/MFA-confirmed self-service deletion, external-media deletion before database removal, session and owned-data cascades, pseudonymous request evidence, mobile privacy center, and non-cacheable API responses. Exit: unit, API, repository, PostgreSQL cascade, mobile, security, coverage, and exact-commit hosted gates pass; the owner-approved privacy policy and retention schedule remain mandatory before production or store submission.
