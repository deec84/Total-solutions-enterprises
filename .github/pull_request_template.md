## Summary

Describe the user outcome and the smallest implementation that delivers it.

## Validation

- [ ] `make validate` passes, or every unavailable local gate is linked to a required CI job.
- [ ] Backend coverage remains at least 90%.
- [ ] Flutter line coverage remains at least 75%.
- [ ] No test is skipped, muted, or marked expected-to-fail to obtain a green result.
- [ ] Database changes include reversible Alembic migration coverage.
- [ ] Security, privacy, provenance, and degraded-state behavior were reviewed.
- [ ] Documentation and `.env.example` were updated when configuration changed.
- [ ] No secret, signing file, state file, plan file, local environment, or generated artifact is included.

## Deployment and rollback

State whether this changes infrastructure, configuration, data, AI behavior, or mobile signing. Link the applicable runbook and describe rollback.
