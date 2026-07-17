# GitHub, staging, and production onboarding

No command in this guide has been executed against an external account. Replace every angle-bracket placeholder only in your secure local session or provider UI; do not commit substituted copies of this document.

## 1. Preflight before Git initialization

From the project root:

```sh
make repository-check
make validate
```

The repository check creates an ephemeral Git index, verifies that credentials and generated artifacts are ignored, confirms required wrappers/lock files are trackable, rejects whitespace errors, and rejects trackable files larger than 50 MB.

Review `.env.example` and confirm there is no real credential. Keep your working `.env` ignored. If Gitleaks is available locally, run `gitleaks dir . --redact`; the hosted Gitleaks job remains mandatory after the first push.

## 2. Create the local repository

```sh
git init -b main
git add --all
git status --short
git diff --cached --check
git commit -m "Initial ParkShield AI platform"
```

Inspect the staged list before committing. It must include `.env.example`, `.terraform.lock.hcl`, `mobile/pubspec.lock`, the Android Gradle Wrapper, documentation, and workflows. It must not include `.env`, `work/`, coverage, build artifacts, Terraform state/plans/tfvars, mobile signing material, or local IDE state.

## 3. Create and connect GitHub

In the selected GitHub organization, create a private repository named `parkshield-ai`. Do not initialize it with another README, `.gitignore`, or license because those choices already exist or require owner approval.

Connect the local repository:

```sh
git remote add origin git@github.com:<OWNER>/parkshield-ai.git
git remote -v
git push -u origin main
```

Equivalent GitHub CLI creation is acceptable after authenticated organization access:

```sh
gh repo create <OWNER>/parkshield-ai --private --source=. --remote=origin --push
```

Do not use a personal access token as an Actions secret. Developer authentication belongs in the developer keychain; Actions receives its short-lived token from GitHub.

## 4. Protect the repository

Create a ruleset for `main` with:

- Pull requests required; no direct pushes or force pushes.
- At least one independent approval, dismissed after new changes.
- Conversation resolution and branch freshness required.
- The `quality` workflow jobs required: `repository`, `backend`, `mobile`, `ios-build`, `container`, `compose-smoke`, and `secrets`.
- The CodeQL `python` job required when available for the repository plan.
- The Terraform job required for infrastructure changes.
- Administrators included in the rule except documented break-glass recovery.

Enable Dependabot alerts/updates, secret scanning, push protection, code scanning, and private vulnerability reporting. If a private-repository CodeQL entitlement is unavailable, that is a recorded production blocker; do not remove the workflow.

After the organization team slug and code owners are known, add a real `.github/CODEOWNERS` file and require its review. Do not commit a placeholder owner that silently routes reviews to nobody. Select a repository license only after the legal owner approves it; the current private source intentionally does not invent one.

## 5. Create GitHub environments

Create `staging`, `production`, and `mobile-production`.

- Require reviewers for `production` and `mobile-production`.
- Prevent self-review where the organization supports it.
- Restrict deployment branches to protected `main`.
- Keep environment variables and secrets separate.
- Do not allow environment bypass merely to make a workflow pass.

Populate `staging` and `production` with the seven variables listed in `docs/environment-variables.md`. Provider passwords/tokens stay in AWS Secrets Manager, not GitHub.

Populate `mobile-production` with three variables and eight signing secrets. Use the GitHub UI or pipe secret values to `gh secret set --env mobile-production`; never place secret values directly in command history.

## 6. Bootstrap each AWS account

Use AWS Organizations/IAM Identity Center and an MFA-protected operator. Prefer distinct staging and production accounts.

Before application Terraform:

1. Enable account-level audit logging, budgets, security contacts, and break-glass controls.
2. Create the encrypted/versioned Terraform S3 state bucket and DynamoDB lock table.
3. Create the GitHub OIDC provider and a deployment role whose trust subject is limited to `repo:<OWNER>/parkshield-ai:environment:<ENVIRONMENT>` and audience `sts.amazonaws.com`.
4. Give that role only the scoped ECR/ECS task-registration, run-task, update-service, describe/wait, and required `iam:PassRole` permissions used by `deploy.yml`.
5. Create the ECR repository with vulnerability scanning, immutable tags where compatible with the workflow, lifecycle policy, and the chosen cross-account promotion/replication policy.
6. Create or delegate the Route 53 hosted zone and validate the regional ACM certificate for the planned origin hostname.
7. Create one Secrets Manager secret per SMTP password, push token, and tow token.
8. Obtain explicit provider egress CIDRs; Terraform rejects unrestricted `0.0.0.0/0`.

Use AWS SSO locally; do not create long-lived access keys for GitHub.

## 7. Prepare staging

Build and push an ARM64 bootstrap image to ECR, capture its digest, and use the full digest URI as `image_uri`. Do this only after local and hosted quality gates are green for the commit.

Copy `infrastructure/terraform/staging.tfvars.example` outside the repository, replace every placeholder, then initialize the dedicated staging state:

```sh
terraform -chdir=infrastructure/terraform init \
  -backend-config="bucket=<STAGING_STATE_BUCKET>" \
  -backend-config="key=staging/core.tfstate" \
  -backend-config="region=<AWS_REGION>" \
  -backend-config="dynamodb_table=<STAGING_LOCK_TABLE>" \
  -backend-config="encrypt=true"

terraform -chdir=infrastructure/terraform plan \
  -var-file=/secure/path/staging.tfvars \
  -out=/secure/path/staging.tfplan
```

Review the plan for account ID, environment name, ingress/egress, secret ARNs, deletion behavior, DNS, cost, and resource count. Store neither the tfvars nor plan in the repository. Apply only after approval:

```sh
terraform -chdir=infrastructure/terraform apply /secure/path/staging.tfplan
```

After apply, set GitHub `staging` variables from Terraform outputs:

```sh
terraform -chdir=infrastructure/terraform output -raw api_base_url
terraform -chdir=infrastructure/terraform output -raw ecs_cluster
terraform -chdir=infrastructure/terraform output -raw ecs_service
terraform -chdir=infrastructure/terraform output -raw ecs_network_configuration
```

Confirm the SNS subscription, run the protected `deploy` workflow for `staging`, execute the documented registration/login/map/assessment/alert/report smoke journey, run a backup/restore drill, and observe alarms/SLOs before considering production.

## 8. Prepare production

Production is a separate approval, not a renamed staging state.

1. Repeat bootstrap in the production account with distinct state, OIDC role, secrets, DNS, certificate, network range, and provider credentials.
2. Copy `production.tfvars.example` to a secure path outside the repository and use it to prepare the reviewed production tfvars file.
3. Require multi-AZ RDS, deletion protection, 35-day backups, protected environment reviewers, confirmed operational alerts, and current restore evidence.
4. Use a commit and image digest that passed staging. Replicate/copy that image into the production `ECR_REPOSITORY` without changing its digest, then supply the full production-repository `@sha256` URI through the deployment workflow's required production `image_uri` input.
5. Apply Terraform only after plan approval.
6. Populate the `production` GitHub variables from production outputs.
7. Run the protected deployment workflow, verify readiness and the critical journey, then monitor the rollback window.
8. Configure `mobile-production` only after backend URL, contracted map tiles, legal metadata, store accounts, and signing custody are approved.

Do not run a signed mobile workflow or store submission merely to test whether credentials work. Use the unsigned iOS and debug Android CI gates until release authorization exists.

## Ordered owner checklist

- [ ] Choose the GitHub organization and private repository owner.
- [ ] Run `make repository-check` and `make validate`.
- [ ] Initialize Git, inspect the staged set, and create the first local commit.
- [ ] Create the empty GitHub repository and push `main`.
- [ ] Enable rulesets, Actions, security features, and required checks.
- [ ] Add approved CODEOWNERS and license/ownership metadata after the responsible teams are known.
- [ ] Create `staging`, `production`, and `mobile-production` environments.
- [ ] Create staging and production AWS accounts and SSO access.
- [ ] Bootstrap remote Terraform state, OIDC roles, ECR, Route 53, and ACM.
- [ ] Contract SMTP, push, tow, map, and official-data providers; collect stable egress ranges.
- [ ] Store provider secrets in AWS Secrets Manager and complete secure tfvars outside Git.
- [ ] Build the approved bootstrap image, review/apply staging Terraform, and populate GitHub variables.
- [ ] Run every hosted quality/security/native gate and the staging smoke/restore evidence.
- [ ] Prepare the isolated production account and approve digest-preserving promotion.
- [ ] Create Apple/Google store identities and load protected signing material only after release approval.
- [ ] Deploy or release only when every applicable gate is green for the exact commit and artifact digest.
