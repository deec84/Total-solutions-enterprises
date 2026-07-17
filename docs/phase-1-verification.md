# Phase 1 verification

## Acceptance matrix

| Control | Result in this workspace | CI control |
| --- | --- | --- |
| Python source parses | Passed | Backend job |
| YAML manifests parse | Passed | Container/backend jobs consume them |
| Backend lint and strict types | Toolchain unavailable locally | `ruff check`, `mypy app` |
| Backend contract tests and coverage | Toolchain unavailable locally | `pytest`, 90% threshold |
| Flutter analysis and widget tests | Flutter unavailable locally | `flutter analyze`, `flutter test` |
| Container build and health check | Docker unavailable locally | Image build job; local Compose run required |

The phase is code-complete but must not be promoted as operationally accepted until all CI jobs pass and a developer completes the Compose health check with a non-default local password.

## Manual Compose check

1. Copy `.env.example` to `.env` and replace both `change-me` values.
2. Run `docker compose config` and confirm no secret is printed in shared logs.
3. Run `docker compose up --build --wait`.
4. Confirm `/api/v1/health/live`, `/api/v1/health/ready`, and `/openapi.json` return HTTP 200.
5. Run `docker compose down`; preserve the named volume unless a deliberate data reset is required.
