# External accounts, credentials, and services

This is the exact external dependency inventory. None of these accounts or credentials is simulated by the repository. Items marked **blocked** require an owner-created account, contract, credential, data grant, or infrastructure action.

## Mandatory account and service inventory

| External dependency | What must be created | Credential or artifact | Approved location | Blocks |
|---|---|---|---|---|
| GitHub organization/account | Private `parkshield-ai` repository, Actions enabled, environments, ruleset, Dependabot, private vulnerability reporting | Developer SSH key or GitHub CLI login; GitHub-managed `GITHUB_TOKEN` | Developer keychain / GitHub | All hosted gates and collaboration |
| GitHub security entitlement | Code scanning for the chosen repository visibility and organization plan | No application secret | GitHub organization settings | Required CodeQL evidence for private repos if the plan does not include it |
| AWS organization | Prefer separate staging and production accounts with billing, budgets, CloudTrail, MFA-protected break-glass access, and IAM Identity Center | Operator SSO assignments | AWS IAM Identity Center | Terraform plan/apply and runtime |
| GitHub-to-AWS federation | GitHub OIDC provider plus one least-privilege deployment role per environment | Role ARN only | GitHub environment variable | Image push, ECS migration, deployment, rollback |
| Terraform backend | Encrypted/versioned S3 state bucket, KMS key or bucket-managed KMS policy, DynamoDB lock table, access logging, deletion protection | Backend names; operator/OIDC authorization | Secure bootstrap records, never source-controlled tfvars | Any safe Terraform apply |
| Amazon ECR | One image repository and lifecycle/scanning policy; cross-account replication or a documented promotion strategy | Repository URL; image digest | GitHub variable / Terraform input | Initial Terraform apply and deployments |
| DNS and TLS | Registered domain, Route 53 public hosted zone, regional ACM certificate for each origin hostname, DNS validation | Hosted-zone ID and certificate ARN | Secure tfvars / GitHub variables as documented | ALB/CloudFront origin TLS |
| Transactional email | AWS SES or contracted SMTP provider, verified domain/sender, dedicated service account | Host, username, password | Metadata in tfvars; password in Secrets Manager | Verification and password recovery; deployed startup |
| Push gateway | Contracted HTTPS gateway able to route Android/iOS tokens; normally backed by Firebase Cloud Messaging and Apple Push Notification service | Endpoint, bearer token; provider-specific FCM/APNs credentials | Endpoint in tfvars; token in Secrets Manager; provider credentials at gateway | Deployed startup and server-originated push delivery |
| Tow lookup provider | Contracted municipal/aggregator gateway satisfying the documented JSON contract and privacy terms | HTTPS endpoint, bearer token, fixed egress CIDRs | Endpoint/CIDRs in tfvars; token in Secrets Manager | Towing recovery in staging/production |
| Map tile provider | Commercial/contracted HTTPS tile service with US coverage, SLA, attribution, quotas, and app-restricted public token if needed | Tile template and restricted public token | `MAP_TILE_URL` GitHub variable | Release mobile builds |
| Store verification gateway | Contracted or organization-owned gateway that validates Apple/Google signed evidence, app account tokens, product IDs, status, expiry, revocation, and environment | Fixed HTTPS endpoint, bearer token, fixed egress CIDRs | Endpoint/CIDRs in tfvars; token in Secrets Manager | Enabling billing or granting paid entitlements |
| Official parking data | Municipal regulations, zones, tow records, facility data, update schedule, usage rights, provenance owner, expiry policy | Owner-approved data grant and feed endpoint; API credential only if the future approved fetch adapter needs one | Provider vault/data pipeline, not Git | Enabling the prepared import source as official, trustworthy launch data, and geographic expansion |
| Apple Developer Program | Organization team, bundle ID `ai.parkshield.parkshieldMobile`, App Store Connect app and subscription products, agreements/tax/banking, StoreKit server notifications, APNs capability if selected, distribution certificate, provisioning profile | Team/product IDs, server-verification material, `.p12`, password, `.mobileprovision` | Secrets Manager / protected GitHub environment plus offline recovery custody | Real native purchases, signed iOS release, and App Store submission |
| Google Play Console | Organization account, application ID `ai.parkshield.parkshield_mobile`, subscription products, payments profile, real-time developer notifications, Play App Signing enrollment, upload key | Product IDs, verification service identity, upload `.jks`, alias and passwords | Workload identity/Secrets Manager / protected GitHub environment plus offline recovery custody | Real native purchases, signed Android release, and Play submission |
| Operational contacts | Monitored alarm email, security contact, support contact, privacy owner, incident commander rotation | Email/group identities | Organization directory and AWS SNS | Alert confirmation, incident response, store/legal readiness |
| Legal/privacy approval | Privacy policy URL and version, terms, retention schedule, location/background-consent review, deletion exceptions, provider DPAs and data rights | Approved documents and URLs | Controlled document system / public site | Production and store approval |

An OpenAI or other hosted LLM account is **not required** by the current implementation. Parking decisions use deterministic verified-data rules and the documented conservative local predictor. Introducing a hosted AI provider would require a separate architecture, privacy, safety, cost, and data-processing review.

## AWS resources created by the application Terraform

Once bootstrap dependencies exist, the checked-in stack creates environment-specific networking, private ECS/Fargate, encrypted RDS PostgreSQL 16, the PostGIS-capable schema through Alembic, generated RDS/JWT secrets, KMS keys, the reserved media bucket, ALB, Route 53 origin record, CloudFront VPC origin, WAF, autoscaling, CloudWatch logs/dashboards/alarms, and SNS.

Terraform intentionally does not create the AWS account, remote state backend, GitHub OIDC bootstrap role, ECR bootstrap repository, public hosted zone, ACM validation prerequisites, provider accounts, or signing identities. Those resources must exist before the first apply.

## Credential values to collect

For each of `staging` and `production`, collect:

1. AWS account ID and region.
2. Terraform state bucket, state key, lock-table name, and KMS/bucket encryption control.
3. GitHub OIDC deployment role ARN.
4. ECR repository URL.
5. Route 53 hosted-zone ID, origin hostname, and validated regional ACM certificate ARN.
6. SMTP host, username, verified sender, password-secret ARN, and fixed network range.
7. Push endpoint, token-secret ARN, and fixed network range.
8. Tow endpoint, token-secret ARN, and fixed network range.
9. When billing is approved: verification endpoint, token-secret ARN, fixed network range, and exact Apple/Google product IDs.
10. Operational alarm email and confirmed SNS subscription.
11. A reviewed, out-of-repository `.tfvars` file containing only approved values and secret ARNs.

For `mobile-production`, collect the three variables and eight secrets listed in `docs/environment-variables.md`, plus contracted store metadata and privacy URLs.

## Explicitly blocked tasks

- Creating or configuring the GitHub repository, rulesets, environments, or organization entitlements.
- Assigning the real GitHub CODEOWNERS team and approving repository license/ownership metadata.
- Running hosted Actions and obtaining exact-commit PostGIS, Compose, container, iOS, CodeQL, and Gitleaks evidence.
- Creating AWS accounts, remote state, ECR, OIDC roles, DNS, certificates, Secrets Manager values, or applying Terraform.
- Contracting SMTP, push, tow, map, and municipal-data providers or obtaining their stable egress ranges.
- Accepting Apple/Google developer and paid-app agreements; selecting prices, trial/refund/tax terms, creating products, connecting native store billing and server notifications, and running real sandbox purchase/revocation tests.
- Approving a municipal source's usage rights, official status, field mapping, freshness policy, data-quality owner, and monitored staging import. Source registration alone is not proof that a feed is official.
- Adding provider-specific native push configuration; the provider and its security model must be selected first.
- Producing signed Android/iOS artifacts, store submissions, or releases.
- Approving the production privacy-policy version, jurisdiction-specific deletion exceptions, and final retention schedule.
- Authorizing staging or production promotion.

These are real gates. They must remain blocked until the named owner supplies the corresponding account, credential, contract, or approval.
