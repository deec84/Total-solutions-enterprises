# SLO and alerting runbook

## Initial objectives

- API availability: 99.9% successful service time per calendar month.
- Cached parking decision latency: p95 below 500 ms; infrastructure warning threshold is one second for five minutes.
- Readiness: at least one healthy target at all times.
- Database: CPU below 80% sustained and free storage above 5 GiB.
- AI safety: zero known false-safe decisions when an applicable official hard-stop rule exists.

## Triage

The `${environment}-operations` CloudWatch dashboard contains request volume, target 5xx, p95 latency, ECS CPU/memory, database saturation, and recent structured 5xx logs. SNS routes alarms to the protected on-call destination.

For 5xx or healthy-target alarms, inspect ECS deployment events and readiness before application logs. For latency, compare ALB latency with ECS saturation and database connections. For database alarms, stop nonessential jobs, verify storage autoscaling/connection pressure, and escalate before making capacity changes. A safety invariant alert always follows the SEV-1 path and disables the implicated model/rule version until reviewed.

Review SLOs monthly. Alert thresholds are operational signals, not permission to consume the full error budget. Record false positives and tune only with measured evidence and approval.
