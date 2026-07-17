# Security policy

Do not disclose a suspected vulnerability in a public issue, discussion, log, screenshot, or pull request.

Use GitHub private vulnerability reporting after it is enabled for the repository. If that channel is unavailable, contact the organization-designated ParkShield security owner through the internal directory. Do not send production credentials or full personal/location data with the initial report.

Include affected version or commit, impact, reproducible steps using synthetic data, and any safe mitigation. Maintainers must preserve evidence, follow `docs/runbooks/incident-response.md`, rotate exposed material, and coordinate disclosure before publishing details.

Only supported code on protected `main` and currently deployed release digests receives security fixes. Dependency, CodeQL, Gitleaks, Bandit, pip-audit, Trivy, and platform security gates must not be bypassed during remediation.
