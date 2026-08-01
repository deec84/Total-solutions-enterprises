#!/usr/bin/env python3
"""Fail closed when GitHub/AWS hardening contracts regress."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
PINNED_ACTION = re.compile(
    r"^\s*(?:-\s+)?uses:\s+([^\s@]+)@([0-9a-f]{40})\s+#\s+(\S.*)$"
)
ANY_ACTION = re.compile(r"^\s*(?:-\s+)?uses:\s+([^\s@]+)@([^\s#]+)")


def require(fragment: str, text: str, source: str, errors: list[str]) -> None:
    if fragment not in text:
        errors.append(f"{source}: missing required hardening fragment: {fragment}")


def main() -> int:
    errors: list[str] = []
    workflow_texts: dict[str, str] = {}

    for path in sorted(WORKFLOW_DIR.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        workflow_texts[path.name] = text
        if "pull_request_target" in text:
            errors.append(f"{path}: pull_request_target is prohibited")
        if "write-all" in text:
            errors.append(f"{path}: write-all is prohibited")
        if "stageing" in text:
            errors.append(f"{path}: misspelled staging environment")

        for line_number, line in enumerate(text.splitlines(), start=1):
            action = ANY_ACTION.match(line)
            if action is None:
                continue
            pinned = PINNED_ACTION.match(line)
            if pinned is None:
                errors.append(
                    f"{path}:{line_number}: action must use a full SHA and version comment"
                )

    combined = "\n".join(workflow_texts.values())
    checkout_count = combined.count("uses: actions/checkout@")
    credential_opt_out_count = combined.count("persist-credentials: false")
    if checkout_count != credential_opt_out_count:
        errors.append(
            "every checkout action must set persist-credentials: false "
            f"({checkout_count} checkouts, {credential_opt_out_count} opt-outs)"
        )

    deploy = workflow_texts.get("deploy.yml", "")
    for fragment in (
        "permissions: {}",
        "github.ref == 'refs/heads/main'",
        "id-token: write",
        "allowed-account-ids: ${{ vars.AWS_ACCOUNT_ID }}",
        "environment:\n      name: ${{ inputs.environment }}",
    ):
        require(fragment, deploy, ".github/workflows/deploy.yml", errors)
    for name, text in workflow_texts.items():
        if name != "deploy.yml" and "id-token: write" in text:
            errors.append(f"{name}: only deploy.yml may request an OIDC token")

    dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    if re.search(
        r"package-ecosystem:\s*docker\s+directory:\s*/(?:\s|$)", dependabot
    ):
        errors.append(".github/dependabot.yml: root Docker ecosystem has no manifest")
    for directory in (
        "/backend",
        "/mobile",
        "/infrastructure/terraform",
        "/mobile/android",
    ):
        require(directory, dependabot, ".github/dependabot.yml", errors)

    versions = (ROOT / "infrastructure" / "terraform" / "versions.tf").read_text(
        encoding="utf-8"
    )
    require('backend "s3"', versions, "infrastructure/terraform/versions.tf", errors)
    require("use_lockfile = true", versions, "infrastructure/terraform/versions.tf", errors)
    require("encrypt      = true", versions, "infrastructure/terraform/versions.tf", errors)

    for environment in ("staging", "production"):
        trust_path = (
            ROOT / "infrastructure" / "aws" / f"oidc-trust-{environment}.json.example"
        )
        trust = trust_path.read_text(encoding="utf-8")
        subject = (
            "repo:deec84/Total-solutions-enterprises:environment:" + environment
        )
        require(subject, trust, str(trust_path.relative_to(ROOT)), errors)
        require("sts.amazonaws.com", trust, str(trust_path.relative_to(ROOT)), errors)

    if errors:
        print("GitHub hardening checks failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("GitHub and infrastructure hardening checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
