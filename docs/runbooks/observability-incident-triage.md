# Observability incident triage

## Start safely

1. Declare the incident level and owner using the incident-response runbook.
2. Open the environment operations dashboard and record the alert name, first
   firing time, deployment digest, affected category, and bounded outcome.
3. Correlate one failing request using `request_id`, `correlation_id`, or
   `trace_id`. Never paste authorization headers, cookies, receipts, precise
   locations, request/response bodies, screenshots, or user records into chat,
   tickets, dashboards, or incident notes.
4. Compare request rate, 5xx rate, p95 latency, readiness, ECS saturation,
   database health, and classified provider failures. A missing configured
   exporter is a readiness failure, not evidence that the service is healthy.

## Containment by signal

- **Readiness or healthy targets:** inspect the last task transition and
  database reachability. If an external telemetry mode was enabled without its
  injected adapter, revert that configuration through the normal protected
  deployment workflow.
- **Parking Score/sign/community regression:** preserve official-data
  precedence, disable the implicated optional predictor/provider flag, and
  never weaken a safety rule to restore throughput.
- **External integration failures:** identify the provider and operation from
  the classified log. Validate DNS/TLS/egress and provider status outside the
  application; do not increase egress to `0.0.0.0/0`.
- **Analytics rejections:** confirm deployment and consent flags, schema
  versions, and prohibited-field rejection. Do not widen event schemas during
  an incident. Disable product analytics if unauthorized data is suspected.
- **Suspected data leakage:** treat as a privacy/security incident, disable the
  affected exporter, preserve access/audit evidence without copying sensitive
  payloads, notify the privacy/security owners, and follow contractual breach
  procedures.

## Recovery and verification

Restore only through a reviewed change. Confirm live and ready probes, all four
golden signals, the affected feature metric, a synthetic non-sensitive trace,
and alert recovery. For analytics, exercise consent denial, user-event deletion,
and expiry purge against staging before re-enabling a durable provider.

Document the root cause, error-budget impact, detection gap, bounded samples,
configuration change, and follow-up owner. Secrets seen during response must be
rotated through the secret-rotation runbook; never place their values in the
postmortem.
