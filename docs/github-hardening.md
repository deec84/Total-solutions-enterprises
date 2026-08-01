# GitHub and infrastructure hardening runbook

This runbook applies to `deec84/Total-solutions-enterprises`. It does not authorize a deployment, release, Terraform apply, secret creation, or production change.

## Correct the accidental staging environment

The repository was observed with `stageing`, `production`, and `mobile-production`; workflows reference the correct name `staging`. GitHub environments cannot be renamed safely as an atomic operation, so use a create-verify-delete sequence:

1. Open **Settings → Environments** and record screenshots or an audit note for `production` and `mobile-production`; do not edit either environment.
2. Open `stageing` and confirm it has no secrets, variables, required reviewers, deployment history, active wait timer, or branch policy that must be migrated.
3. Search the repository and workflow history for `stageing`. The source gate rejects that spelling under `.github/workflows` and `infrastructure`.
4. Create a new environment named exactly `staging`.
5. Leave `staging` secrets and variables empty. Select **Selected branches and tags**, add the single branch rule `main`, and add no tag rule. Confirm the active ruleset protects `main`. Disable administrator bypass where the repository plan supports it.
6. Do not run the deployment workflow. Verify `production` and `mobile-production` are unchanged.
7. Only after steps 2–6 are recorded, delete the empty `stageing` environment.
8. Re-open **Settings → Environments** and confirm the exact set is `staging`, `production`, and `mobile-production`.

Do not populate `staging` until an AWS account, reviewed OIDC role, Terraform state bootstrap, cost approval, and secure environment-variable handoff exist.

## Actions policy

Repository Actions settings should use a read-only default `GITHUB_TOKEN`, disable write tokens and secrets for fork pull requests, and require actions to be pinned to a full-length commit SHA. Allow only the action repositories currently referenced by reviewed workflows:

- `actions/checkout`, `actions/setup-python`, and `actions/upload-artifact`;
- `github/codeql-action`;
- `hashicorp/setup-terraform`;
- `aquasecurity/trivy-action` and `gitleaks/gitleaks-action`;
- `docker/setup-buildx-action` and `docker/build-push-action`;
- `subosito/flutter-action` while Flutter remains transitional;
- `aws-actions/configure-aws-credentials`, `aws-actions/amazon-ecr-login`, and `aws-actions/amazon-ecs-render-task-definition`.

Every `uses:` reference is pinned to a verified 40-character commit with its readable release tag in a comment. Dependabot remains responsible for proposing later SHA changes through ordinary reviewed PRs.

## Main ruleset

The effective `main` protection must require a pull request, one independent approval, dismissal of stale approvals, conversation resolution, a current branch, no force pushes, no deletion, and no bypass except a documented break-glass identity. Require these hosted checks by their stable job names:

- `repository`, `backend`, `mobile`, `ios-build`, `container`, `compose-smoke`, and `secrets` from `quality`;
- `python` from `codeql`;
- `terraform` from `infrastructure` when infrastructure, observability, or its gate changes.

If overlapping rulesets exist, consolidate them only after comparing their combined effective protections. Never remove a gate merely to eliminate duplication.

## Deployment workflow boundary

`deploy.yml` is manual-only, rejects every ref except `refs/heads/main`, accepts only `staging` or `production`, uses environment protection, grants `id-token: write` only to its deployment job, validates all non-secret inputs before requesting AWS credentials, and assumes an exact environment-bound OIDC role. Production requires an immutable staging-approved digest and the production role has no image-push permission.

The protected environment must supply eight non-secret variables documented in `environment-variables.md`. Provider secrets remain in AWS Secrets Manager. No workflow uses static AWS keys.

## Existing Dependabot PRs requiring manual review

The following open PRs were observed on 2026-08-01. The hardening configuration does not merge, approve, close, or recreate them:

| PR | Change | Review class |
|---:|---|---|
| #1 | `configure-aws-credentials` 6.1.1 → 6.2.2 | Superseded by the verified 6.2.2 SHA in this hardening branch; confirm the PR closes after merge rather than merging it separately. |
| #2 | `upload-artifact` 4 → 7 | Major Actions runtime change; verify runner compatibility and artifact semantics. |
| #3 | ECS task-definition renderer 1.8.5 → 1.9.0 | Deployment action; verify task JSON output and rollback flow. |
| #5 | Gitleaks action 2 → 3 | Major security-gate change; verify licensing, token use, and detection parity. |
| #6 | Python container 3.12 → 3.14 | Runtime migration; run full backend, image, integration, and performance gates. |
| #7 | pytest-cov upper bound 7 → 8 | Major test tooling; confirm unchanged coverage arithmetic. |
| #8 | cryptography upper bound 49 → 50 | Security library major; review compatibility and audit output. |
| #9 | mypy upper bound 2 → 3 | Major type-checker change; no error suppression permitted. |
| #10 | Buildx action 3 → 4 | Major supply-chain action; verify provenance/SBOM behavior. |
| #11 | Flutter lints 4 → 6 | Transitional client lint migration; do not weaken rules. |
| #12 | Kotlin plugin 2.3.20 → 2.4.10 | Transitional Android wrapper; verify Flutter build compatibility. |
| #13 | Gradle wrapper 9.1.0 → 9.6.1 | Build tool update; validate wrapper checksum and Android build. |
| #21 | Android Gradle Plugin 9.0.1 → 9.3.1 | Build-system update; validate SDK, lint, package, and device compatibility. |
| #22 | AWS provider 6.55.0 → 6.56.0 | Review changelog, lock hashes, validate, Trivy, and a credential-free plan where possible. |
| #24 | Flutter local notifications 22.0.1 → 22.2.0 | Permission/background behavior; physical-device regression required. |

Dependabot now targets only real manifests: pip `/backend`, pub `/mobile`, Actions `/`, Docker `/backend`, Terraform `/infrastructure/terraform`, and Gradle `/mobile/android`. Minor and patch updates are grouped per ecosystem, concurrent PRs are bounded, and no automerge is configured. The invalid root Docker ecosystem has been removed.

## Manual publication from the isolated local clone

If Codex cannot access the macOS keychain, the prepared branch can be published from the operator's Terminal without sharing a credential:

```sh
cd /Users/davidecheverria/Documents/Codex/parkshield-ai-github-hardening
git status --short --branch
git log -1 --oneline
git push -u origin agent/github-infrastructure-hardening
gh pr create --draft --base main --head agent/github-infrastructure-hardening \
  --title "Harden GitHub and infrastructure boundaries" \
  --body-file /secure/path/parkshield-hardening-pr.md
```

Review the exact branch and commit before pushing. Do not mark the PR ready, merge it, dispatch releases, or run Terraform apply as part of this procedure.
