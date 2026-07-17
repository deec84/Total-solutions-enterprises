# Phase 11 — Deployment and operations

## Delivered controls

- AWS infrastructure as code for isolated staging/production VPCs, private ARM64 ECS tasks, encrypted PostgreSQL, KMS/S3, CloudFront/WAF, autoscaling, backups, centralized secrets, logs, dashboards, and alarms.
- Immutable digest-based container promotion through GitHub OIDC, protected environments, forward-only migrations, ECS circuit breaker, readiness smoke test, and service rollback.
- Signed Android App Bundle and iOS IPA workflows using ephemeral protected signing material and release-only HTTPS configuration validation.
- Terraform formatting/provider validation, dependency/security CI, PostGIS migration/integration gates, native mobile builds, and backup/restore drills.
- Git-safe onboarding preflight, local Compose migration orchestration, hosted Compose/PostGIS smoke verification, Route 53 origin creation, and exact ECS network outputs for GitHub environments.
- Staging may build a digest-pinned ARM64 image; production rejects mutable/tag-only input and requires the approved digest in its configured ECR repository.
- Runbooks for release/rollback, incidents, SLO alerts, backup/restore, and secret rotation.

## Production boundary

Source and automation are ready for account-specific provisioning. Actual production promotion requires organization-owned AWS accounts, DNS/provider contracts, SMTP/push/tow-provider accounts, municipal parking data, store signing identities, protected GitHub environment approvals, and successful CI/apply evidence. These external credentials and datasets are intentionally not embedded or simulated.

## Local verification

Terraform validates against AWS provider 6.55.0 and Trivy reports zero high/critical IaC findings. GitHub workflows pass Actionlint 1.7.12, Flutter Analyze reports no issues, all 40 Flutter tests pass with 77.61% line coverage against the new 75% gate, the Android debug APK builds, and the iOS export plist is valid. Docker/PostGIS and the full Xcode application remain unavailable, so Linux database/container and macOS iOS Actions jobs stay required and are not allowed to fail.
