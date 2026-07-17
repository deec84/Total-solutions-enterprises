# Deployment and rollback runbook

## Release gate

1. Confirm quality, CodeQL, infrastructure, native Android/iOS, PostGIS integration, backup/restore, and secret-scanning checks are green for the exact commit.
2. Review backward compatibility. Schema changes use expand/migrate/contract; a release must be safe with both the previous and next application revision.
3. Deploy to `staging`, complete registration/login/map/AI/notification/community smoke tests, and observe error rate and p95 latency for at least 15 minutes.
4. Replicate the exact staging-approved digest into the production ECR repository, obtain the protected `production` approval, and dispatch the same commit with that full `@sha256` URI in `image_uri`.

For staging, the workflow can publish an immutable ARM64 image. Production rejects an empty or tag-based `image_uri` and deploys only the supplied digest from its configured ECR repository. The workflow records the previous ECS task definition, runs `alembic upgrade head` as a one-off task, deploys through the ECS circuit breaker, and calls `/api/v1/health/ready` through CloudFront.

## Automatic rollback

If migration succeeds but rollout/readiness fails, the workflow restores the previous task definition and waits for stability. It does not reverse the database migration. Forward migrations must therefore remain backward compatible.

## Manual rollback

1. Declare an incident and freeze further deployments.
2. Identify the last healthy task definition from ECS deployment history and the audit trail.
3. Run `aws ecs update-service --cluster CLUSTER --service api --task-definition PREVIOUS_ARN` using the break-glass role.
4. Wait for `aws ecs wait services-stable`, then verify liveness, readiness, login, map, and Parking AI official hard-stop behavior.
5. If the schema itself caused harm, prefer a corrective forward migration. Database point-in-time recovery requires incident-command approval because it can discard valid writes.
6. Preserve logs, task events, image digest, migration revision, timestamps, and operator actions. Complete a blameless review within five business days.
