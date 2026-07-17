# Incident response runbook

## Severity and ownership

- **SEV-1:** unsafe parking guidance, confirmed sensitive-data exposure, widespread outage, or destructive data loss. Page incident commander, security, engineering, product, and legal/privacy immediately.
- **SEV-2:** major feature unavailable, elevated errors/latency, delayed notifications, or incorrect non-official estimates. Page the owning engineer and incident commander.
- **SEV-3:** localized degradation with a workaround. Create an owned ticket and monitor.

## Response

1. Acknowledge the SNS alarm, open an incident channel/timeline, assign incident commander and communications lead, and record UTC timestamps.
2. Protect users first. Disable affected AI/provider paths, preserve official-data hard stops, revoke exposed sessions/secrets, or roll back the service as appropriate.
3. Use request IDs to correlate privacy-safe application logs with ALB/ECS/RDS metrics. Do not paste user photos, tokens, precise location histories, or credentials into incident chat.
4. Preserve CloudWatch, WAF, audit-chain, ECS event, database, and deployment evidence under the incident retention policy.
5. Communicate status at least every 30 minutes for SEV-1 and hourly for SEV-2. Legal/privacy owns regulatory and user-notification decisions.
6. Verify recovery with readiness plus representative auth, official-rule, notification, and community workflows. Continue monitoring through a stable observation window.
7. Rotate temporary access, close break-glass sessions, document root cause and detection gaps, and assign dated corrective actions.

For suspected audit-chain tampering or an AI false-safe result against official restrictions, treat the event as SEV-1 even if only one user is known to be affected.
