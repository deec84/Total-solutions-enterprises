# Configuration and environment variables

No real secret belongs in Git, Terraform variable files, workflow YAML, Dart source, Docker layers, tickets, or logs. `.env.example` contains placeholders only. Local values go in ignored `.env`; deployed values go in AWS Secrets Manager or protected GitHub environments as specified below.

## Backend variables

All backend names use the `PARKSHIELD_` prefix.

| Variable | Required | Sensitive | Purpose and constraints |
|---|---:|---:|---|
| `PARKSHIELD_ENVIRONMENT` | Yes | No | `local`, `test`, `staging`, or `production`. Deployed modes enable fail-closed validation. |
| `PARKSHIELD_LOG_LEVEL` | No | No | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`; default `INFO`. |
| `PARKSHIELD_API_V1_PREFIX` | No | No | API prefix; default `/api/v1`. Change only with coordinated mobile and gateway updates. |
| `PARKSHIELD_JWT_SECRET` | Yes outside tests | Yes | JWT signing and application-field encryption key. Deployed value must be random, non-default, and at least 32 characters. |
| `PARKSHIELD_ACCESS_TOKEN_TTL_MINUTES` | No | No | Access-token lifetime; default `15`. |
| `PARKSHIELD_REFRESH_TOKEN_TTL_DAYS` | No | No | Refresh-token lifetime; default `30`. |
| `PARKSHIELD_DATABASE_URL` | Yes | Yes | SQLAlchemy async PostgreSQL URL. Deployed URL must be non-local and include `ssl=require`. |
| `PARKSHIELD_SMTP_HOST` | Deployed | No | SMTP hostname. |
| `PARKSHIELD_SMTP_PORT` | No | No | SMTP port; default `587`; the adapter uses STARTTLS. |
| `PARKSHIELD_SMTP_USERNAME` | Deployed | Usually | Dedicated SMTP service-account name. |
| `PARKSHIELD_SMTP_PASSWORD` | Deployed | Yes | SMTP credential; AWS Secrets Manager in staging/production. |
| `PARKSHIELD_EMAIL_FROM` | Yes | No | Provider-verified sender address. |
| `PARKSHIELD_MOBILE_LINK_SCHEME` | No | No | Deep-link scheme; default `parkshield`. |
| `PARKSHIELD_PUSH_PROVIDER_URL` | Deployed | No | HTTPS endpoint for the contracted push gateway. |
| `PARKSHIELD_PUSH_PROVIDER_TOKEN` | Deployed | Yes | Bearer token for the push gateway; AWS Secrets Manager. |
| `PARKSHIELD_TOW_PROVIDER_URL` | Deployed | No | HTTPS endpoint for the contracted tow lookup gateway. |
| `PARKSHIELD_TOW_PROVIDER_TOKEN` | Deployed | Yes | Bearer token for the tow gateway; AWS Secrets Manager. |

Terraform injects `PARKSHIELD_MEDIA_BUCKET` into ECS as a reserved bucket name. The current privacy-preserving community flow hashes photos and discards raw bytes, so the application does not yet consume that setting. Durable media retention remains disabled until an approved object-store adapter and deletion policy are implemented.

## Docker Compose-only variables

These values configure the local container topology; they are not backend `Settings` fields.

| Variable | Sensitive | Default/purpose |
|---|---:|---|
| `PARKSHIELD_API_PORT` | No | Host port mapped to API port 8000; default `8000`. |
| `PARKSHIELD_POSTGRES_PORT` | No | Host port mapped to PostgreSQL 5432; default `5432`. |
| `PARKSHIELD_POSTGRES_DB` | No | Local database name; default `parkshield`. |
| `PARKSHIELD_POSTGRES_USER` | No | Local database role; default `parkshield`. |
| `PARKSHIELD_POSTGRES_PASSWORD` | Yes | Local database password. It must match the password embedded in `PARKSHIELD_DATABASE_URL`. |

## Flutter compile-time definitions

Flutter reads these with `String.fromEnvironment`; supply them with `--dart-define` at build time.

| Definition | Sensitive | Requirement |
|---|---:|---|
| `PARKSHIELD_API_BASE_URL` | No | Local HTTP is accepted for debug. Release requires an absolute HTTPS URL. |
| `PARKSHIELD_MAP_TILE_URL` | Public/restricted token possible | HTTPS template containing `{z}`, `{x}`, and `{y}`. Release rejects the public OSM host. Any public map token must be restricted by app identifier, origin, quota, and least privilege. |

Do not place a server-side map secret in a mobile binary. Mobile tokens are extractable and must be provider-designated public tokens with restrictions.

## Terraform inputs

Terraform values are supplied through a secure out-of-repository `.tfvars` file or an approved automation system. They are not application environment variables.

| Input | Sensitive | Source |
|---|---:|---|
| `aws_region` | No | Chosen regional workload location; default `us-east-1`. |
| `environment` | No | `staging` or `production`. |
| `image_uri` | No | Existing ECR image URI pinned with `@sha256:`. |
| `desired_count` | No | ECS task count; default `2`. |
| `alarm_email` | Personal/operational | Monitored address that confirms the SNS subscription. |
| `smtp_host`, `smtp_username`, `email_from` | Account metadata | Contracted email provider. |
| `smtp_password_secret_arn` | ARN only | Existing Secrets Manager secret containing only the SMTP password. |
| `push_provider_url` | No | Contracted HTTPS push endpoint. |
| `push_provider_token_secret_arn` | ARN only | Existing Secrets Manager secret containing only the push token. |
| `tow_provider_url` | No | Contracted HTTPS towing endpoint. |
| `tow_provider_token_secret_arn` | ARN only | Existing Secrets Manager secret containing only the tow token. |
| `provider_egress_cidrs` | No | Fixed provider network ranges. Must not contain `0.0.0.0/0`. |
| `origin_domain_name` | No | Route 53 origin hostname covered by the regional ACM certificate. |
| `route53_zone_id` | No | Existing public hosted-zone ID for the origin hostname. |
| `origin_certificate_arn` | No | Regional ACM certificate ARN covering the origin hostname. |
| `vpc_cidr` | No | Environment VPC range; default `10.42.0.0/16`; environments must not overlap if peered. |

Terraform generates the RDS password and JWT secret and stores them in Secrets Manager. Terraform state therefore contains sensitive material and must use an encrypted, versioned, access-logged remote backend.

## GitHub environment variables

Create both `staging` and `production` environments with these non-secret variables:

| Variable | Value source |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | Least-privilege GitHub OIDC deployment role in that AWS account. |
| `AWS_REGION` | Terraform `aws_region`. |
| `ECR_REPOSITORY` | Full ECR repository URL without a tag. |
| `ECS_CLUSTER` | `terraform output -raw ecs_cluster`. |
| `ECS_SERVICE` | `terraform output -raw ecs_service`. |
| `ECS_NETWORK_CONFIGURATION` | `terraform output -raw ecs_network_configuration`. |
| `API_BASE_URL` | `terraform output -raw api_base_url`. |

No long-lived AWS access key is used. Do not create `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` GitHub secrets.

Create `mobile-production` with these variables:

- `API_BASE_URL`
- `MAP_TILE_URL`
- `APPLE_TEAM_ID`

And these protected secrets:

- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`
- `ANDROID_STORE_PASSWORD`
- `IOS_DISTRIBUTION_CERTIFICATE_BASE64`
- `IOS_DISTRIBUTION_CERTIFICATE_PASSWORD`
- `IOS_PROVISIONING_PROFILE_BASE64`
- `IOS_KEYCHAIN_PASSWORD`

`GITHUB_TOKEN` is generated automatically by GitHub Actions. Do not create or copy it manually.

## Storage rules

| Value | Approved storage |
|---|---|
| Local development secrets | Ignored `.env` on the developer machine. |
| SMTP, push, and tow tokens | One single-value AWS Secrets Manager secret per provider and environment. |
| RDS password and JWT key | Terraform-managed AWS Secrets Manager secrets. |
| AWS deployment authentication | GitHub OIDC role; no static keys. |
| Terraform state | Dedicated encrypted/versioned S3 backend with DynamoDB locking and restricted operators. |
| Android/Apple signing material | Protected `mobile-production` GitHub environment and organization-controlled offline recovery custody. |
| Public mobile map token | GitHub environment variable with provider-side application and quota restrictions. |
