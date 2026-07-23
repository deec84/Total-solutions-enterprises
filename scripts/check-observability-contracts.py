#!/usr/bin/env python3
"""Fail CI when observability-as-code loses required signals or privacy limits."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_METRICS = {
    "http_requests_total",
    "http_errors_total",
    "http_request_duration_ms",
    "authentications_total",
    "municipal_imports_total",
    "sign_analyses_total",
    "parking_score_queries_total",
    "community_events_total",
    "billing_verifications_total",
    "integration_failures_total",
    "product_analytics_events_total",
    "product_analytics_rejections_total",
}
FORBIDDEN_DIMENSIONS = {
    "email",
    "user_id",
    "latitude",
    "longitude",
    "location",
    "token",
    "receipt",
    "password",
}


def load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise SystemExit(f"{path}: schema_version must be 1")
    return value


dashboard = load_json(ROOT / "observability/dashboards/parkshield-overview.json")
panels = dashboard.get("panels")
if not isinstance(panels, list):
    raise SystemExit("observability dashboard panels must be a list")
metrics: set[str] = set()
dimensions: set[str] = set()
for panel in panels:
    if not isinstance(panel, dict):
        raise SystemExit("every dashboard panel must be an object")
    metrics.update(str(item) for item in panel.get("metrics", []))
    dimensions.update(str(item) for item in panel.get("dimensions", []))
missing = REQUIRED_METRICS - metrics
if missing:
    raise SystemExit(f"observability dashboard is missing metrics: {sorted(missing)}")
prohibited = FORBIDDEN_DIMENSIONS & dimensions
if prohibited:
    raise SystemExit(f"observability dashboard has sensitive dimensions: {sorted(prohibited)}")

alerts = load_json(ROOT / "observability/alerts/slo-rules.json")
rules = alerts.get("rules")
if not isinstance(rules, list) or len(rules) < 4:
    raise SystemExit("at least four SLO alert contracts are required")
for rule in rules:
    if not isinstance(rule, dict):
        raise SystemExit("every alert rule must be an object")
    required = {"name", "sli", "objective", "window_days", "page", "runbook"}
    if required - set(rule):
        raise SystemExit(f"alert rule is incomplete: {rule.get('name', 'unknown')}")
    objective = rule["objective"]
    if not isinstance(objective, (int, float)) or not 0 < objective <= 1:
        raise SystemExit(f"alert objective is invalid: {rule.get('name', 'unknown')}")

print("Observability dashboard, metrics, privacy dimensions, and SLO contracts are valid.")
