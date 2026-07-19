# Secret rotation runbook

JWT, database, SMTP, push, mobile-signing, and AWS break-glass credentials have named owners and rotation schedules. Secrets are stored only in Secrets Manager or protected GitHub environments; Terraform variables and state backends must never receive provider password values.

For SMTP/push rotation, create a new secret version, test it in staging, update the ECS task definition, deploy, verify delivery, then revoke the old value. For a suspected exposure, rotate immediately and preserve evidence before revocation where safe.

The billing-gateway bearer token follows the same create-test-promote-revoke sequence and must be exercised only with sandbox evidence in staging. The billing-subject HMAC key protects pseudonymous user, transaction, and event references and cannot be replaced in place: introduce dual-key lookup, backfill every retained reference in a reviewed migration, verify idempotency/reconciliation, then retire the old key. An uncoordinated rotation would orphan idempotency references and is prohibited.

JWT rotation affects active tokens. Introduce dual-key verification before changing the signing key when planned; during compromise, rotate immediately and revoke all sessions. Database rotation requires a coordinated new credential, Secrets Manager update, fresh tasks, connection drain, and verification before the old credential is disabled.

Android keystores and Apple certificates/profiles are changed only through the protected `mobile-production` environment. Verify store continuity and recovery custody before replacing signing material.
