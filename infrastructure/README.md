# ParkShield infrastructure

Terraform provisions isolated `staging` and `production` AWS environments. The stack uses CloudFront, WAF, an ALB, private ECS Fargate tasks, encrypted PostgreSQL 16, Secrets Manager, KMS/S3, autoscaling, CloudWatch logs/dashboards, and SNS alarms.

## State bootstrap

Create a dedicated state bucket and customer-managed KMS key outside this stack for each environment. Enable bucket versioning, public-access blocking, TLS enforcement, access logging or CloudTrail data events, and tightly scoped recovery access. Terraform 1.12 uses the S3-native `.tflock` object; DynamoDB locking is deprecated and is not used. Operators authenticate through IAM Identity Center and GitHub uses an environment-bound OIDC role; never create long-lived AWS keys.

Copy the matching example backend file outside the repository, replace its placeholders, and initialize with that secure file so one state can never address both environments:

```sh
terraform -chdir=terraform init \
  -backend-config=/secure/path/backend.staging.hcl
```

Terraform state contains generated database/JWT/billing-subject material and must be treated as a production secret. Never use local state for a deployed environment.

## Required inputs

Copy the matching `terraform/staging.tfvars.example` or `terraform/production.tfvars.example` outside the repository and replace every placeholder. `image_uri` must use an ECR digest (`@sha256:`). SMTP, push, and municipal tow-lookup tokens must already exist as single-value Secrets Manager secrets; Terraform receives only their ARNs. Billing remains false by default; enabling it additionally requires an approved HTTPS verification gateway, its single-value token-secret ARN, and at least one real store product ID. Provider egress CIDRs must include only exact approved ranges and cannot be the full internet. The public Route 53 hosted zone and validated regional ACM origin certificate are bootstrap dependencies; Terraform creates the origin alias record.

```sh
terraform -chdir=terraform fmt -check -recursive
terraform -chdir=terraform init -backend=false
terraform -chdir=terraform validate
terraform -chdir=terraform plan -var-file=/secure/path/staging.tfvars -out=staging.plan
terraform -chdir=terraform apply staging.plan
```

Use separate AWS accounts when available. Production plans require peer review, a protected GitHub environment, current backup evidence, and a green staging smoke test. The deployment workflow performs a forward migration, ECS circuit-breaker rollout, readiness test, and service-revision rollback.

## GitHub environment configuration

Backend environments (`staging`, `production`) require `AWS_ACCOUNT_ID`, `AWS_DEPLOY_ROLE_ARN`, `AWS_REGION`, `ECR_REPOSITORY`, `ECS_CLUSTER`, `ECS_SERVICE`, `ECS_NETWORK_CONFIGURATION`, and `API_BASE_URL` variables. Both environments accept deployments only from protected `main`; protect production with independent required reviewers.

Populate `ECS_NETWORK_CONFIGURATION` directly from `terraform output -raw ecs_network_configuration`; do not hand-edit subnet/security-group JSON.

The `mobile-production` environment requires API/map variables plus Android keystore and Apple distribution/provisioning secrets documented in `mobile/README.md`. No signing material belongs in source control.

The exact OIDC trust and least-privilege policy templates are in `aws/`. The complete account bootstrap and external-service inventory is in `../docs/repository-onboarding.md` and `../docs/external-services.md`.
