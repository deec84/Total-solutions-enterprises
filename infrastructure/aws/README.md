# AWS bootstrap boundaries

These files are reviewable templates, not provisioned resources. Replace angle-bracket placeholders only in a secure operator workspace. Never commit the substituted files, account identifiers, role names, or credentials.

## GitHub OIDC

Create one GitHub OIDC provider and one deployment role in each isolated AWS account. The audience is `sts.amazonaws.com`. Each trust policy requires the exact repository/environment subject and `refs/heads/main` claim:

- staging: `repo:deec84/Total-solutions-enterprises:environment:staging`
- production: `repo:deec84/Total-solutions-enterprises:environment:production`

Use `oidc-trust-staging.json.example` and `oidc-trust-production.json.example`. Do not add branch, repository-wide, wildcard-environment, pull-request, or fork subjects. The trust policy and `deploy` workflow both reject every ref except `refs/heads/main`, and the job binds to the selected protected GitHub environment.

Attach the matching deployment permission template. The staging role may push only to the staging ECR repository. The production role intentionally has no ECR push permission because production accepts only a staging-approved digest already present in the production repository. Replace every placeholder with a reviewed ARN, run IAM Access Analyzer, and narrow any action further when AWS reports resource-level support.

No `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` belongs in GitHub. The only AWS identity input is the non-secret `AWS_DEPLOY_ROLE_ARN`; GitHub exchanges its environment-bound OIDC assertion for short-lived credentials.

## Terraform state bootstrap

Create the state resources outside the application stack because Terraform cannot store its state in a bucket that does not exist yet. Use a dedicated bucket and customer-managed KMS key per AWS account and environment. Required controls:

- S3 Block Public Access and Bucket owner enforced;
- versioning enabled before first state write;
- default SSE-KMS encryption with a dedicated, rotating key;
- TLS-only bucket policy and access logging or CloudTrail data events;
- no cross-environment principals and no object-delete permission on the state key;
- bounded administrator and break-glass access through IAM Identity Center;
- recovery test from a previous object version before application infrastructure is approved.

Terraform 1.12 uses the S3-native `.tflock` object through `use_lockfile = true`. DynamoDB locking is deprecated and is not part of this design. The example state policy grants delete permission only to the lock object, not to state.

Copy the appropriate `backend.*.hcl.example` to an untracked secure directory, replace placeholders, authenticate using AWS IAM Identity Center, and initialize with:

```sh
terraform -chdir=infrastructure/terraform init \
  -backend-config=/secure/path/backend.staging.hcl
```

Do not put AWS credentials in the backend file or command line. Do not run `apply` until the account, cost, plan, recovery, and change approvals are recorded.
